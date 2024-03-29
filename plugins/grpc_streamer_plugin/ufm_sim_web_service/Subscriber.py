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
from google.protobuf.any_pb2 import Any
import google.protobuf.timestamp_pb2
import requests
import time
from datetime import datetime
from threading import Lock
import grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2
from Config import RESTCall,Constants


class Subscriber:
    """
    For manage the client job, request get calls and threads (thread in streaming for each api call).
    The grpc server uses this class to manage the rest calls, This is for one client in server.

    The Functions call the rest api of the ufm once or in a stream.
    for each result from the get calls create gRPCStreamerParams message to send by the server.
    """
    job_id_messages = 1
    lock = Lock()

    def __init__(self, ip, rest_api_calls, session, host):
        """
        :param ip: name/ip of machine that asked this information
        :param rest_api_calls: list of (tuples/list) that represent the wanted calls i.e
        [('Events', 10, False), ['Alarms', 25, False]]
        :param session: session that allow it to get rest data
        :param host: the host of machine of the ufm
        """
        self.dest_ip = ip
        self.calls = []
        self.threads = []
        self.stop_all = False
        self._session = session
        self._host = host
        self.__processing_calls(rest_api_calls)
        self.queue = None
        self.callback = None

    def __processing_calls(self, rest_api_calls):
        """
        extract the information from rest calls
        :param rest_api_calls: list of (tuples/list) that represent the wanted calls i.e
        [('Events', 10, False), ['Alarms', 25, False]]
        We want the user to have the ability to use both list and tuple for easier communication with the server.
        :return:
        """
        if rest_api_calls is None: return
        for call in rest_api_calls:
            is_tuple = isinstance(call, tuple) or isinstance(call, list)
            name = call[0] if is_tuple else call
            name = name.capitalize()
            if RESTCall.__contains__(name):
                interval = int(call[1]) if len(call) > 1 and is_tuple else Constants.REST_DEFAULT_INTERVAL
                delta = bool(call[2]) if len(call) > 2 and is_tuple else Constants.REST_DEFAULT_DELTA

                location = RESTCall[name].location # get the location from the rest call.
                tuple_data = (name, interval, delta, location)
                self.calls.append(tuple_data)
            else:
                print(f'{name} could not be added, it is not in rest apis')

    def thread_task(self, call, queue, callback, session):
        """
        function for the threading calling, extract new data if dalta is True in the call
        :param call: one of the call in self.calls (we want the thread to be in the server and not here)
        :param queue: queue to put the new data in.
        :param callback: callback queue to put a new call for a function to release the wait.
        :return:
        """
        name, interval, delta, location = call[0], call[1], call[2], RESTCall[call[0]].location
        last_id = None
        self.queue = queue
        self.callback = callback
        while not self.stop_all:
            result = self.__send_get_request(location, session)
            if result.status_code != 200:
                break
            if delta:
                result, last_id = self.extract_new_data(result.json(), last_id)
            else:
                result = result.json()

            message = self._encode_results_(name, result)
            queue.put(message) # sending the result to main thread
            if callback:
                callback.put(self.new_data_callback) # calling a callback to get this result
            time.sleep(interval) # sleep for interval time


    def new_data_callback(self):
        return self.dest_ip

    def extract_new_data(self, results, last_id):
        """
        if id is inside the message and delta is on, retrieve only messages after the previous latest id
        :param results: all data got from rest call.
        :param last_id: previous latest id.
        :return: part of results that is after that id.
        """
        #tolikin builds delta function
        output = []
        if len(results) == 0 or "id" not in results[0]:
            return results, 0

        next_last_id = 0 if last_id is None else last_id #get the last id or 0

        #bring only the apis after that id
        for item in results:
            if int(item["id"]) > next_last_id:
                output.append(item)
                next_last_id = max(item["id"], next_last_id)
        return output, next_last_id

    def all_result(self,session):
        """
        get all the data from all the calls and return them in messages
        :return: list of encoded messages
        """
        messages = []
        for call in self.calls:
            respond = self.__send_get_request(call[3],session)
            if respond is None:
                continue
            if respond.status_code != 200:
                continue
            data = respond.json()
            if not isinstance(data, list):
                continue
            messages.append((call[0], str(data)))

        output = []
        for message in messages:
            output.append(self._encode_results_(message[0], message[1]))

        return output

    def serialization(self):
        """
        retrieve messages of all the calls that in the destination and send messages to the queue.
        :return:
        """
        if not(self.callback and self.queue):
            return
        for call in self.calls:
            respond = self.__send_get_request(call[3])
            if respond.status_code != 200:
                continue
            data = respond.json()

            message = self._encode_results_(call[0], str(data))
            self.queue.put(message)  # sending the result to main thread
            if len(data) > 0 and self.callback:
                self.callback.put(self.new_data_callback)

    def to_message(self):
        """
        encode destination to grpc DestinationParams
        :return: DestinationParams of self
        """
        params = []
        for item in self.calls:
            params.append(grpc_plugin_streamer_pb2.SubscriberParams.APIParams(ufm_api_name=item[0],
                                                                               interval=item[1], only_delta=item[2]))
        if len(self.calls) == 0:
            raise Exception(Constants.LOG_NO_REST_SUBSCRIBER)
        return grpc_plugin_streamer_pb2.SubscriberParams(job_id=self.dest_ip, apiParams=params)

    def _encode_results_(self, task_name, data):
        """
        encode message to be grpc gRPCStreamerParams
        :param task_name: the call/task that the message came from
        :param data: data of the message
        :return: gRPCStreamerParams of given data and task_name
        """
        des_message = grpc_plugin_streamer_pb2.gRPCStreamerParams()
        des_message.ufm_api_name = task_name
        des_message.data = str(data)
        timestamp = google.protobuf.timestamp_pb2.Timestamp()
        timestamp.FromDatetime(datetime.now())
        des_message.timestamp.CopyFrom(timestamp)
        des_message.message_id = str(Subscriber.job_id_messages)
        with Subscriber.lock:
            Subscriber.job_id_messages += 1
        return des_message

    def __send_get_request(self,resource_path, session):
        """
        get rest call from the path that was given
        :param resource_path: path to the api we want to get
        :return: respond from get
        """
        if self._host is None or session is None:return None
        addition=''
        if 'Authorization' in session.headers:
            addition = "V3"
        else:
            addition = ""
        if ':' in self._host:
            url = 'https://[{0}]{1}{2}'.format(self._host, '/ufmRest'+addition, resource_path)
        else:
            url = 'https://{0}{1}{2}'.format(self._host, '/ufmRest'+addition,resource_path)
        try:
            respond = session.get(url)
            return respond
        except requests.ConnectionError as e:
            print("Wasn't able to reach " + resource_path + ". Connection Error, please see this exception.\n" + str(e))
        except requests.Timeout as e:
            print("Wasn't able to reach " + resource_path + ". Timeout Error, please see this exception.\n" + str(e))
        except requests.RequestException as e:
            print("Wasn't able to reach " + resource_path + ". Request Error, please see this exception.\n" + str(e))
        except KeyboardInterrupt as e:
            print("Wasn't able to reach " + resource_path + ". Connection Error, please see this exception.\n" + str(e))
        return None
