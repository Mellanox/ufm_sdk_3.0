#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
import argparse
import os.path
import threading
import time
import grpc
import requests
import queue
import logging

import google.protobuf.empty_pb2

import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2_grpc as grpc_plugin_streamer_pb2_grpc
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2
from concurrent import futures
from logging.handlers import RotatingFileHandler
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Destination import Destination
from plugins.grpc_streamer_plugin.ufm_sim_web_service.GRPCMessageConverter import *

from plugins.grpc_streamer_plugin.ufm_sim_web_service.Config import Constants,GENERAL_UTILS
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)


class StopStream(Exception):
    def __init__(self, message):
        super(StopStream, self).__init__(message)


class GRPCPluginStreamerServer(grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceServicer):

    def __init__(self,host=None):
        self.callbacks = {}
        self.feeds = {}
        self.destinations = {}
        self.subscribeDict_queue = {}
        self._session = {}
        #self.__create_session__(host, port, auth)
        if host:
            self.config_server(host)
        else:
            self.parse_args()
        self.create_logger(Constants.CONF_LOGFILE_NAME)

    def config_server(self,host):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_plugin_streamer_pb2_grpc.add_GeneralGRPCStreamerServiceServicer_to_server(self, self.server)

        grpc_port = Constants.UFM_PLUGIN_PORT
        self.port_dest = f"[::]:{grpc_port}"
        self.server.add_insecure_port(self.port_dest)

        self._host = host
        self._port = Constants.UFM_HTTP_PORT  # web https

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-h', '--host', action='store', dest='host_ip', default=None, help="Host ip")
        args = parser.parse_args()
        self._host = args.host_ip
        self.config_server(self._host)

    def create_logger(self, file):
        format_str = "%(asctime)-15s UFM-gRPC-Streamer-{0} Machine: {1}     %(levelname)-7s: %(message)s".format(file,self._host)
        conf_file = GENERAL_UTILS.getGrpcStreamConfFile()
        self.log_name = Constants.DEF_LOG_FILE

        logging.basicConfig(format=format_str,level=logging.INFO)
        rotateHandler = RotatingFileHandler(self.log_name,maxBytes=10*1024*1024,backupCount=5)
        rotateHandler.setLevel(logging.INFO)
        rotateHandler.setFormatter(logging.Formatter(format_str))
        logging.getLogger('').addHandler(rotateHandler)

    def start(self):
        logging.info(Constants.LOG_SERVER_START %self._host)
        self.server.start()

    def stop(self):
        logging.info(Constants.LOG_SERVER_STOP%self._host)
        self.server.stop(0)

    def __create_session__(self,client, auth):
        self._session[client] = requests.Session()
        self._session[client].auth = auth
        self._session[client].verify = False
        self._session[client].headers.update({'Content-Type': 'application/json; charset=utf-8',"X-Remote-User": "ufmsystem"})
        self._session.get(self._host)
        if ':' in self._host:
            url = 'https://[{0}]{1}'.format(self._host, '/ufmRestV2')
        else:
            url = 'https://{0}{1}'.format(self._host, '/ufmRestV2')
        try:
            result = self._session.get(url)
            if result.status_code == 200:
                logging.info(Constants.LOG_CREATE_SESSION % client)
                return "Success"
            logging.info(Constants.LOG_CANNOT_UFM%result.status_code)
            return Constants.LOG_CANNOT_UFM + str(result.status_code)
        except requests.ConnectionError as e:
            logging.error(Constants.LOG_CANNOT_UFM%str(e))
            return Constants.LOG_CANNOT_SESSION + str(e)
        except Exception as e:
            logging.error(Constants.LOG_CANNOT_UFM % str(e))
            return Constants.LOG_CANNOT_SESSION + str(e)

    def CreateSession(self, request, context):
        ip = request.client_user
        auth = (request.username,request.password)
        result = self.__create_session__(ip, auth)
        return grpc_plugin_streamer_pb2.SessionRespond(respond=result)

    def GetJobParams(self, request, context):
        ip = request.job_id
        logging.info(Constants.LOG_GET_PARAMS%ip)
        job = self.destinations.get(ip, None)
        return encode_destination(job)

    def ListDestinations(self, request, context):
        logging.info(Constants.LOG_LIST_DESTINATION)
        messages = []
        for key in self.destinations:
            messages.append(encode_destination(self.destinations[key]))

        return grpc_plugin_streamer_pb2.ListDestinationParams(destinations=messages)

    def AddDestination(self, request, context):
        ip, param_results = decode_destination(request)
        respond = grpc_plugin_streamer_pb2.SessionRespond()
        if ip not in self._session:
            respond.respond = Constants.LOG_CANNOT_DESTINATION + Constants.LOG_CANNOT_NO_SESSION
            logging.error(respond.respond)
            return respond

        if ip in self.destinations:
            respond.respond = "WE ALREADY HAVE IT:" + ip
            logging.info(Constants.LOG_CANNOT_DESTINATION+Constants.LOG_EXISTED_DESTINATION%ip)
        elif len(param_results) == 0:
            respond.respond = Constants.LOG_NO_REST_DESTINATION
            logging.info(Constants.LOG_CANNOT_DESTINATION+Constants.LOG_NO_REST_DESTINATION)
        else:
            self.destinations[ip] = Destination(ip, param_results, self._session[ip], self._host)
            respond.respond = "Created user with session, added new ip:" + ip
            logging.info(Constants.LOG_CREATE_DESTINATION % ip)
        return respond

    def Help(self,request,context):
        return grpc_plugin_streamer_pb2.SessionRespond(respond=Constants.PLUGIN_HELP)

    def Version(self, request, context):
        return self.Help(request,context)

    def RunOnceJob(self, request, context):
        ip = request.job_id
        logging.info(Constants.LOG_RUN_JOB_ONCE%ip)
        if ip not in self._session:
            return grpc_plugin_streamer_pb2.runOnceRespond(job_id=("Cant create client without session,"
                                                                   " please use CreateSession first. Need to create a session"), results=[])
        if ip not in self.destinations:
            return grpc_plugin_streamer_pb2.runOnceRespond(job_id=("WE DONT HAVE THIS TO RUN:" + ip), results=[])

        job = self.destinations[ip]
        messages = job.all_result()
        return grpc_plugin_streamer_pb2.runOnceRespond(job_id=str(messages[0].job_id), results=messages)

    def EditDestination(self, request, context):
        ip, param_results = decode_destination(request)
        logging.info(Constants.LOG_EDIT_DESTINATION%ip)
        if ip not in self._session:
            return grpc_plugin_streamer_pb2.SessionRespond(respond=Constants.ERROR_NO_SESSION)
        self.destinations[ip] = Destination(ip,param_results, self._session[ip], self._host)
        return grpc_plugin_streamer_pb2.SessionRespond(respond="")

    def DeleteDestination(self, request, context):
        ip = request.job_id
        logging.info(Constants.LOG_DELETE_DESTINATION%ip)
        if ip in self.destinations:
            self.destinations.pop(ip)
        else:
            print("WE COUDLN'T FIND AND REMOVE THIS ID:"+ip)
            logging.error(Constants.LOG_NO_EXIST_DESTINATION%ip)
        return google.protobuf.empty_pb2.Empty()

    def RunOnce(self, request, context):
        ip, param_results = decode_destination(request)
        logging.info(Constants.LOG_RUN_ONCE%ip)
        if ip not in self._session:
            logging.error(Constants.ERROR_NO_SESSION)
            return grpc_plugin_streamer_pb2.runOnceRespond(job_id=Constants.ERROR_NO_SESSION, results=[])
        destination = Destination(ip,param_results, self._session[ip], self._host)
        messages = destination.all_result()
        return grpc_plugin_streamer_pb2.runOnceRespond(job_id=messages[0].job_id, results=messages)

    def RunPeriodically(self, request, context):
        ip, calls = decode_destination(request)
        logging.info(Constants.LOG_RUN_STREAM%ip)
        if ip not in self._session:
            logging.error(Constants.ERROR_NO_SESSION)
            return grpc_plugin_streamer_pb2.gRPCStreamerParams(data=Constants.ERROR_NO_SESSION)
        dest = Destination(ip, calls, self._session[ip], self._host)
        self.callbacks[ip] = self.__stream_configuration(context, dest)
        return self.__output_generator(ip,context)

    def RunStreamJob(self, request, context):
        ip = request.job_id
        logging.info(Constants.LOG_RUN_JOB_Periodically%ip)
        dest = self.destinations[ip] if ip in self.destinations else None
        self.callbacks[ip] = self.__stream_configuration(context, dest)
        return self.__output_generator(ip,context)

    def SubscribeToStream(self, request, context):
        ip = request.job_id
        logging.info(Constants.LOG_CALL_SUBSCRIBE%ip)
        if ip in self.subscribeDict_queue:
            self.subscribeDict_queue[ip].append(context)
        else:
            self.subscribeDict_queue[ip] = [context]
        self.callbacks[context] = self.__stream_configuration(context, ip, ip)
        return self.__output_generator(ip, context, True)

    def StopStream(self, request, context):
        ip = request.job_id
        logging.info(Constants.LOG_CALL_STOP_STREAM%ip)
        if ip in self.destinations:
            self.destinations[ip].stop_all = True
            self.callbacks[ip].put(StopStream)
        else:
            print("CANT STOP STREAM, cant find "+str(ip))
            logging.info(Constants.LOG_NO_EXIST_DESTINATION%ip)
        return google.protobuf.empty_pb2.Empty()

    def Serialization(self, request, context):
        logging.info(Constants.LOG_CALL_SERIALIZATION)
        for ip in self.destinations:
            self.destinations[ip].serialization()

        return google.protobuf.empty_pb2.Empty()

    def __output_generator(self, ip,context,sucsriber=False):
        logging.info(Constants.LOG_START_STREAM%ip)
        if ip not in self._session:
            logging.error(Constants.ERROR_NO_SESSION)
            yield grpc_plugin_streamer_pb2.gRPCStreamerParams(data=Constants.ERROR_NO_SESSION)
            return

        if ip not in self.destinations:
            logging.error(Constants.ERROR_NO_CLIENT)
            yield grpc_plugin_streamer_pb2.gRPCStreamerParams(data=Constants.ERROR_NO_CLIENT)
            return
        while True:
            try:
                try:
                    callback = self.callbacks[ip].get(True)
                    ip = callback()
                except queue.Empty:
                    pass
                if self.feeds.get(context) is not None:
                    while not self.feeds[context].empty():
                        result = self.feeds[context].get()

                        if ip and ip in self.subscribeDict_queue and not sucsriber:
                            for subscriber in self.subscribeDict_queue[ip]:
                                self.feeds[subscriber].put(result)
                                self.callbacks[subscriber].put(self.emptySubscriber)

                        if isinstance(result, grpc_plugin_streamer_pb2.gRPCStreamerParams):
                            yield result
                        else:
                            raise StopStream('stopping stream')


            except IndexError:
                print("That not good")
            except StopStream:
                print("stopping thread:"+str(context))

                return

    def __stream_configuration(self, context, dest, subscribeTo=None):
        self.feeds[context] = queue.Queue()
        callbacks = queue.Queue()

        def stop_stream():
            logging.info(Constants.LOG_STOP_STREAM)
            if self.feeds.get(context) is not None:
                del self.feeds[context]

            def raise_stop_stream_exception():
                raise StopStream('stopping stream')

            callbacks.put(raise_stop_stream_exception)

        if subscribeTo or not dest:
            context.add_callback(stop_stream)
            return callbacks

        threads = [threading.Thread(target=dest.thread_task, args=(call, self.feeds[context], callbacks))
                   for call in dest.calls]
        logging.info(Constants.LOG_START_STREAM%f"start {len(threads)} threads for the ip {dest.dest_ip} of {context}")
        for th in threads:
            th.daemon = True
            th.start()
        context.add_callback(stop_stream)
        return callbacks

    def emptySubscriber(self):
        return None


def main():
    server = GRPCPluginStreamerServer(host='localhost')#'10.209.36.31')
    server.start()
    print("start server")
    try:
        while True:
            time.sleep(84000)
    except KeyboardInterrupt:
        server.stop()
    print("stop server")


if __name__ == '__main__':
    main()
