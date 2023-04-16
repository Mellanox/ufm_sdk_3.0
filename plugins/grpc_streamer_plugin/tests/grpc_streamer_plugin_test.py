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
import grpc
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../ufm_sim_web_service'))
import ufm_sim_web_service.grpc_client as client
import ufm_sim_web_service.grpc_plugin_streamer_pb2_grpc as grpc_plugin_streamer_pb2_grpc
import ufm_sim_web_service.grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2
from ufm_sim_web_service.Subscriber import Subscriber
from google.protobuf.empty_pb2 import Empty
from ufm_sim_web_service.Config import Constants

import sys

DEFAULT_PASSWORD = "admin"
DEFAULT_USERNAME = "admin"


class TestPluginStreamer:
    def __init__(self,HOST_IP):
        self.job_id = 'coco'
        self.host_ip=HOST_IP
        self._client = client.GrpcClient(HOST_IP, Constants.UFM_PLUGIN_PORT, self.job_id)
        self.FAILED_TESTS_COUNT = 0

    def assert_equal(self,message, left_expr, right_expr, test_name="positive"):
        if left_expr == right_expr:
            print("    - test name : {} -- PASS"
                  .format(message))
        else:
            self.FAILED_TESTS_COUNT += 1
            print("    - test name: {}  -- FAIL (expected: {}, actual: {})"
                  .format( message, right_expr, left_expr))


    def testAddSession(self):
        result = self._client.add_session(DEFAULT_USERNAME,DEFAULT_PASSWORD)
        self.assert_equal("create session using default logins",result,True)
        self._client.onceIDApis([('Events'), ("junk")])

    def testAddUser(self):
        self._client.add_session(DEFAULT_USERNAME,DEFAULT_PASSWORD)
        result = self._client.added_job([('Events')])
        self.assert_equal("create destination(client) after session",result,True)
        try:
            channel = grpc.insecure_channel(f'{self.host_ip}:{Constants.UFM_PLUGIN_PORT}')
            stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(channel)
            result = stub.ListSubscribers(Empty())
            self.assert_equal("Rececive a list of clients ",result.__class__.__name__,"ListSubscriberParams")
            self.assert_equal("The amount of clients in the server is 1",len(result.subscribers),1)
        except grpc.RpcError as e:
            self.assert_equal("Error accorded",e,None)

    def testGetOnce(self):
        result = self._client.add_session(DEFAULT_USERNAME, DEFAULT_PASSWORD)
        self.assert_equal("create session using default logins", result, True)
        result = self._client.onceApis([('Events'), ("Alarms")],(DEFAULT_USERNAME, DEFAULT_PASSWORD))
        self.assert_equal("Receive data in get once rest api",result is not None,True)

    def testAddWithoutSession(self):
        dest = Subscriber(self.job_id+"c", [('Events'), ("Alarms")], None, None)
        try:
            channel = grpc.insecure_channel(f'{self.host_ip}:{Constants.UFM_PLUGIN_PORT}')
            stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(channel)
            result = stub.AddSubscriber(dest.to_message())
            channel.close()
            self.assert_equal("Receive respond from add destination",result.__class__.__name__,"SessionRespond")
            self.assert_equal("The message we receive is the same as we plan ",result.respond , Constants.LOG_CANNOT_SUBSCRIBER + Constants.LOG_CANNOT_NO_SESSION)
        except grpc.RpcError as e:
            self.assert_equal("RpcError accorded",e,None)

    def testEmptyDestination(self):
        try:
            self._client.onceApis(['junk'], (DEFAULT_USERNAME, DEFAULT_PASSWORD))
        except Exception as e:
            self.assert_equal("Error have being excepted",str(e),Constants.LOG_NO_REST_SUBSCRIBER)

    def testAllTaskAreRestCalls(self):
        result = self._client.onceApis([('Events'), ("junk")],(DEFAULT_USERNAME, DEFAULT_PASSWORD))
        if result is None:
            self.FAILED_TESTS_COUNT += 1
            print("    - test name: result from onceAPI is a message  -- FAIL (expected: runOnceRespond message, actual: None)")
            return 1
        all_good=0
        for message in result.results:
            all_good+=1 if (message.ufm_api_name == 'Events') else 0

        self.assert_equal("all messages have the right task names",all_good,len(result.results))


def main(HOST_IP):
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    tester = TestPluginStreamer(HOST_IP)
    tester.testEmptyDestination()
    tester.testAddWithoutSession()
    tester.testAddSession()
    tester.testAddUser()
    tester.testGetOnce()
    tester.testAllTaskAreRestCalls()

    if tester.FAILED_TESTS_COUNT > 0:
        print("\n{} tests failed".format(tester.FAILED_TESTS_COUNT))
        return 1
    else:
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='grpc_streamer plugin test')
    parser.add_argument('-ip', '--host', type=str,default="localhost", help='Host IP address where grpc_server plugin is running')
    args = parser.parse_args()
    HOST_IP = args.host

    sys.exit(main(HOST_IP))
