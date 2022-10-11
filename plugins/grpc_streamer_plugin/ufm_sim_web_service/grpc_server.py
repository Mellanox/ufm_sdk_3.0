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
import configparser
import os.path
import threading
import time
import grpc
import requests
import queue
import logging

import google.protobuf.empty_pb2

import grpc_plugin_streamer_pb2_grpc as grpc_plugin_streamer_pb2_grpc
#import ufm_sim_web_service.grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2
from concurrent import futures
from logging.handlers import RotatingFileHandler
from Subscriber import Subscriber
from GRPCMessageConverter import *

from Config import Constants,GENERAL_UTILS
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)


class StopStream(Exception):
    def __init__(self, message):
        super(StopStream, self).__init__(message)


class GRPCPluginStreamerServer(grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceServicer):
    def __init__(self, host=None):
        self.callbacks = {}
        self.feeds = {}
        self.subscribers = {}
        self.subscribeDict_queue = {}
        self._session = {}
        self.parse_config()
        self.config_server(host)
        self.create_logger(Constants.CONF_LOGFILE_NAME)

    def parse_config(self):
        grpc_config = configparser.ConfigParser()
        if os.path.exists(Constants.config_file_name):
            grpc_config.read(Constants.config_file_name)
            Constants.log_level = grpc_config.get("Common","log_level")
            Constants.UFM_PLUGIN_PORT = grpc_config.getint("Common","grpc_port")
            Constants.log_file_max_size = grpc_config.getint("Common","log_file_max_size")
            Constants.log_file_backup_count = grpc_config.getint("Common","log_file_backup_count")
            Constants.grpc_max_workers = grpc_config.getint("Common","grpc_max_workers")


    def config_server(self, host):
        """
        config the server to the ufm that is in the location of host
        :param host: location/ip of the ufm machine
        :return:
        """
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=Constants.grpc_max_workers))
        grpc_plugin_streamer_pb2_grpc.add_GeneralGRPCStreamerServiceServicer_to_server(self, self.server)

        grpc_port = Constants.UFM_PLUGIN_PORT
        self.port_dest = f"[::]:{grpc_port}"
        self.server.add_insecure_port(self.port_dest)

        self._host = host
        self._port = Constants.UFM_HTTP_PORT  # web https


    def create_logger(self, file):
        """
        create a logger to put all the data of the server action
        :param file: name of the file
        :return:
        """
        format_str = "%(asctime)-15s UFM-gRPC-Streamer-{0} Machine: {1}     %(levelname)-7s: %(message)s".format(file,self._host)
        conf_file = GENERAL_UTILS.getGrpcStreamConfFile()
        self.log_name = Constants.DEF_LOG_FILE
        logger = logging.getLogger(self.log_name)

        logging_level=logging.getLevelName(Constants.log_level) \
            if isinstance(Constants.log_level,str) else Constants.log_level

        logging.basicConfig(format=format_str,level=logging_level)
        rotateHandler = RotatingFileHandler(self.log_name,maxBytes=Constants.log_file_max_size,
                                            backupCount=Constants.log_file_backup_count)
        rotateHandler.setLevel(Constants.log_level)
        rotateHandler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(rotateHandler)

    def start(self):
        """
        starts the server
        :return:
        """
        logging.info(Constants.LOG_SERVER_START %self._host)
        self.server.start()

    def stop(self):
        """
        stops the server
        :return:
        """
        logging.info(Constants.LOG_SERVER_STOP%self._host)
        self.server.stop(0)

    def get_port(self):
        #[::]:
        return self.port_dest.split(':')[3]

    def __create_session__(self, client, auth, token):
        """
        create a session for client with the auth and save it
        :param client: given id/ip/client name
        :param auth: username,password
        :return: "success" if successful or message of why it didnt success
        """
        session = requests.Session()
        if token!='':
            session.headers.update({"Authorization": "Basic "+token})
        else:
            session.auth = auth
        session.verify = False
        session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
        end = ('/ufmRest' if token == '' else '/ufmRestV3')+'/app/events'
        if ':' in self._host:
            url = 'https://[{0}]{1}'.format(self._host, end)
        else:
            url = 'https://{0}{1}'.format(self._host, end)
        try:
            result = session.get(url)
            if result.status_code == 200:
                logging.info(Constants.LOG_CREATE_SESSION % client)
                return session, "Success"
            logging.info(Constants.LOG_CANNOT_UFM%result.status_code)
            return None, Constants.LOG_CANNOT_UFM + str(result.status_code)
        except requests.ConnectionError as e:
            logging.error(Constants.LOG_CANNOT_UFM%str(e))
            return None, Constants.LOG_CANNOT_SESSION + str(e)
        except Exception as e:
            logging.error(Constants.LOG_CANNOT_UFM % str(e))
            return None, Constants.LOG_CANNOT_SESSION % str(e)

    def CreateSession(self, request, context):
        """
        service grpc function to create session
        :param request: SessionAuth
        :param context:
        :return: SessionRespond
        """
        ip = request.job_id
        auth = (request.username,request.password)
        session, result = self.__create_session__(ip, auth,str(request.token))
        if session is not None:
            self._session[ip] = session
        return grpc_plugin_streamer_pb2.SessionRespond(respond=result)

    def GetJobParams(self, request, context):
        """
        service grpc function to retrieve Subscriber params by given id
        :param request: gRPCStreamerID
        :param context:
        :return: SubscriberParams
        """
        ip = request.job_id
        logging.info(Constants.LOG_GET_PARAMS%ip)
        job = self.subscribers.get(ip, None)
        return encode_subscriber(job)

    def ListSubscribers(self, request, context):
        """
        service grpc function to get list of all the Subscribers
        :param request: empty
        :param context:
        :return: ListSubscriberParams that have all the Subscribers
        """
        logging.info(Constants.LOG_LIST_SUBSCRIBER)
        messages = []
        for key in self.subscribers:
            messages.append(encode_subscriber(self.subscribers[key]))

        return grpc_plugin_streamer_pb2.ListSubscriberParams(Subscribers=messages)

    def AddSubscriber(self, request, context):
        """
        service grpc function to add new Subscriber
        :param request: SubscriberParams
        :param context:
        :return: SessionRespond of successful or not
        """
        ip, param_results = decode_subscriber(request)
        respond = grpc_plugin_streamer_pb2.SessionRespond()
        if ip not in self._session:
            respond.respond = Constants.LOG_CANNOT_SUBSCRIBER + Constants.LOG_CANNOT_NO_SESSION
            logging.error(respond.respond)
            return respond

        if ip in self.subscribers:
            respond.respond = "WE ALREADY HAVE IT:" + ip
            logging.info(Constants.LOG_CANNOT_SUBSCRIBER+Constants.LOG_EXISTED_SUBSCRIBER%ip)
        elif len(param_results) == 0:
            respond.respond = Constants.LOG_NO_REST_SUBSCRIBER
            logging.info(Constants.LOG_CANNOT_SUBSCRIBER+Constants.LOG_NO_REST_SUBSCRIBER)
        else:
            self.subscribers[ip] = Subscriber(ip, param_results, self._session[ip], self._host)
            respond.respond = "Created user with session, added new ip:" + ip
            logging.info(Constants.LOG_CREATE_SUBSCRIBER % ip)
        return respond

    def Help(self,request,context):
        return grpc_plugin_streamer_pb2.SessionRespond(respond=Constants.PLUGIN_HELP)

    def Version(self, request, context):
        return self.Help(request,context)

    def RunOnceJob(self, request, context):
        """
        service grpc function to run a job once with only the id
        :param request: gRPCStreamerID that contains only id
        :param context:
        :return: runOnceRespond
        """
        ip = request.job_id
        logging.info(Constants.LOG_RUN_JOB_ONCE%ip)
        if ip not in self._session:
            return grpc_plugin_streamer_pb2.runOnceRespond(job_id=Constants.ERROR_NO_SESSION, results=[])
        if ip not in self.subscribers:
            return grpc_plugin_streamer_pb2.runOnceRespond(job_id=Constants.ERROR_NO_CLIENT, results=[])

        job = self.subscribers[ip]
        messages = job.all_result(self._session[ip])
        del self._session[ip]
        if len(messages) == 0:
            return grpc_plugin_streamer_pb2.runOnceRespond(job_id=Constants.ERROR_CONNECTION, results=[])
        return grpc_plugin_streamer_pb2.runOnceRespond(job_id=str(messages[0].message_id), results=messages)

    def EditSubscriber(self, request, context):
        """
        service grpc function to edit a job with new parameters
        :param request: SubscriberParams
        :param context:
        :return: SessionRespond
        """
        ip, param_results = decode_subscriber(request)
        logging.info(Constants.LOG_EDIT_SUBSCRIBER%ip)
        if ip not in self._session:
            return grpc_plugin_streamer_pb2.SessionRespond(respond=Constants.ERROR_NO_SESSION)
        self.subscribers[ip] = Subscriber(ip, param_results, self._session[ip], self._host)
        return grpc_plugin_streamer_pb2.SessionRespond(respond="")

    def DeleteSubscriber(self, request, context):
        """
        service grpc function to delete a job with given id
        :param request: gRPCStreamerID
        :param context:
        :return: Empty
        """
        ip = request.job_id
        logging.info(Constants.LOG_DELETE_SUBSCRIBER%ip)
        if ip in self.subscribers:
            self.subscribers.pop(ip)
        else:
            print("WE COUDLN'T FIND AND REMOVE THIS ID:"+ip)
            logging.error(Constants.LOG_NO_EXIST_SUBSCRIBER%ip)
        return google.protobuf.empty_pb2.Empty()

    def RunOnce(self, request, context):
        """
        service grpc function to run a job once with given all parameters
        :param request: SubscriberParams
        :param context:
        :return: runOnceRespond
        """
        ip, param_results = decode_subscriber(request)
        logging.info(Constants.LOG_RUN_ONCE%ip)
        if ip not in self._session:
            logging.error(Constants.ERROR_NO_SESSION)
            return grpc_plugin_streamer_pb2.runOnceRespond(job_id=Constants.ERROR_NO_SESSION, results=[])
        subscriber = Subscriber(ip, param_results, self._session[ip], self._host)
        messages = subscriber.all_result(self._session[ip])
        del self._session[ip]

        if ip in self.subscribeDict_queue:
            for message in messages:
                for subscriber in self.subscribeDict_queue[ip]:
                    self.feeds[subscriber].put(message)
                    self.callbacks[subscriber].put(self.emptySubscriber)

        return grpc_plugin_streamer_pb2.runOnceRespond(job_id=messages[0].message_id if len(messages)>0 else '0',
                                                       results=messages)

    def RunPeriodically(self, request, context):
        """
        service grpc function to run a job streamed with given all parameters
        :param request: SubscriberParams
        :param context:
        :return: iterator that updates
        """
        ip, calls = decode_subscriber(request)
        logging.info(Constants.LOG_RUN_STREAM%ip)
        dest = Subscriber(ip, calls, self._session[ip], self._host)
        self.callbacks[ip] = self.__stream_configuration(context, dest,self._session[ip])
        return self.__output_generator(ip,context)

    def RunStreamJob(self, request, context):
        """
        service grpc function to run a job streamed with given only id when created before the Subscriber
        :param request: gRPCStreamerID
        :param context:
        :return: iterator that updates
        """
        ip = request.job_id
        logging.info(Constants.LOG_RUN_JOB_Periodically%ip)
        dest = self.subscribers[ip] if ip in self.subscribers else None
        session = self._session[ip]
        self.callbacks[ip] = self.__stream_configuration(context, dest,session)
        return self.__output_generator(ip, context)

    def SubscribeToStream(self, request, context):
        """
        service grpc function to subscribe to ID and recieve also all messages that goes thought that ID
        :param request: gRPCStreamerID
        :param context:
        :return: iterator that updates
        """
        ip = request.job_id
        logging.info(Constants.LOG_CALL_SUBSCRIBE%ip)
        if ip in self.subscribeDict_queue:
            self.subscribeDict_queue[ip].append(context)
        else:
            self.subscribeDict_queue[ip] = [context]
        self.callbacks[context] = self.__stream_configuration(context, ip, None, ip)
        return self.__output_generator(ip, context, True)

    def StopStream(self, request, context):
        """
        service grpc function to stop a stream of given id
        :param request: gRPCStreamerID
        :param context:
        :return: empty
        """
        ip = request.job_id
        logging.info(Constants.LOG_CALL_STOP_STREAM%ip)
        if ip in self.subscribers:
            self.subscribers[ip].stop_all = True
            self.callbacks[ip].put(StopStream)
        else:
            print("CANT STOP STREAM, cant find "+str(ip))
            logging.info(Constants.LOG_NO_EXIST_SUBSCRIBER%ip)
        return google.protobuf.empty_pb2.Empty()

    def Serialization(self, request, context):
        """
        service grpc function to serialize all the streams data
        :param request: empty
        :param context:
        :return: empty
        """
        logging.info(Constants.LOG_CALL_SERIALIZATION)
        for ip in self.subscribers:
            self.subscribers[ip].serialization()

        return google.protobuf.empty_pb2.Empty()

    def __output_generator(self, ip, context, is_subscriber=False):
        """
        Stream Iterator that wait for an update or callback for stopstream
        :param ip: id/ip of job
        :param context:
        :param is_subscriber: if it is a subscribed stream or regular one.
        :return: itrator for messages
        """
        logging.info(Constants.LOG_START_STREAM%ip)
        if ip not in self._session:
            logging.error(Constants.ERROR_NO_SESSION)
            yield grpc_plugin_streamer_pb2.gRPCStreamerParams(data=Constants.ERROR_NO_SESSION)
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

                        if ip and ip in self.subscribeDict_queue and not is_subscriber:
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
                del self._session[ip]
                return

    def __stream_configuration(self, context, dest,session, subscribeTo=None):
        """
        configurate the stream iterator and start the threads
        :param context:
        :param dest: Subscriber we want to work on
        :param subscribeTo: if the stream is subscribe to anther stream
        :return: callback queue for the iterator
        """
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

        threads = [threading.Thread(target=dest.thread_task, args=(call, self.feeds[context], callbacks, session))
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
    server = GRPCPluginStreamerServer(host='localhost')
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
