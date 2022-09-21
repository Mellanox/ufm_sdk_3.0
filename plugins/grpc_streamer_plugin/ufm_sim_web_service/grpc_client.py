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
import grpc
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2_grpc as grpc_plugin_streamer_pb2_grpc
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Destination import Destination
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Config import Constants


class GrpcClient:

    def __init__(self, server_ip, server_port,job_id):
        self.grpc_channel = f'{server_ip}:{server_port}'
        self.job_id = job_id

    def _start_request(self, api_list, auth, solo_add_session=False, solo_add_job=False):
        if solo_add_session:
            if len(auth)<2: return False
            success = self.add_session(auth[0],auth[1])
            if not success: return False

        if solo_add_job:
            success = self.added_job(api_list)
            if not success:
                return False
        try:
            self.channel = grpc.insecure_channel(self.grpc_channel)
            self.stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(self.channel)
        except grpc.RpcError as e:
            print(e)
            return False
        return True

    def _end_request(self):
        self.channel.close()

    def _end_stream(self,interator):
        result_list = []
        for x in interator:
            print(x.data)
            result_list.append(x)

        self.channel.close()

    def add_session(self,username,password):
        try:
            self.channel = grpc.insecure_channel(self.grpc_channel)
            self.stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(self.channel)
            self.stub.CreateSession(grpc_plugin_streamer_pb2.SessionAuth(client_user=self.job_id, username=username,
                                                                     password=password))
            self.channel.close()
            return True
        except grpc.RpcError as e:
            print("Couldnt add a session")
        return False

    def added_job(self, api_list):
        self.dest = Destination(self.job_id, api_list, None, None)
        try:
            self.channel = grpc.insecure_channel(self.grpc_channel)
            self.stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(self.channel)
            self.stub.AddDestination(self.dest.to_message())
            self.channel.close()
        except grpc.RpcError as e:
            return False
        return True

    def onceIDApis(self,api_list, auth=[], solo=False):
        try:
            success = self._start_request(api_list,auth,solo,solo)
            if not success: return None
            result = self.stub.RunOnceJob(grpc_plugin_streamer_pb2.gRPCStreamerID(job_id=self.job_id))
            self._end_request()
            return result
        except grpc.RpcError as e:
            print(e)
            return None

    def onceApis(self,api_list, auth):
        try:
            success = self._start_request(api_list, auth, True, False)
            if not success: return None
            self.dest = Destination(self.job_id, api_list, None, None)
            result = self.stub.RunOnce(self.dest.to_message())
            self._end_request()
            return result
        except grpc.RpcError as e:
            print(e)
            return None

    def streamIDAPIs(self, api_list, auth=[], solo=False):
        try:
            success = self._start_request(api_list,auth,solo,solo)
            if not success: return None
            interator = self.stub.RunStreamJob(grpc_plugin_streamer_pb2.gRPCStreamerID(job_id=self.job_id))
            return self._end_stream(interator)
        except grpc.RpcError as e:
            print(f"client couldnt get stream: {e}")
            return None

    def streamApis(self, api_list, auth):
        try:
            success = self._start_request(api_list, auth, True, False)
            if not success: return None
            self.dest = Destination(self.job_id, api_list, None,None)
            interator = self.stub.RunPeriodically(self.dest.to_message())
            return self._end_stream(interator)
        except grpc.RpcError as e:
            print(f"client couldnt get stream: {e}")
            return None

    def subscribeTo(self, ip):
        try:
            self._start_request([],[],False,False)
            interator = self.stub.SubscribeToStream(grpc_plugin_streamer_pb2.gRPCStreamerID(job_id=ip))
            return self._end_stream(interator)
        except grpc.RpcError as e:
            print(f"client couldnt connect: {e}")
            return False


class Runner():
    def runOnce(self):
        client = GrpcClient('localhost', str(Constants.UFM_PLUGIN_PORT), 'local')
        result = client.onceIDApis([("Events", 10, True), ("Alarms", 10, True), ("Links", 40, False), ("stuff")])
        print(result)


    def runStream(self):
        client = GrpcClient('localhost', str(Constants.UFM_PLUGIN_PORT), 'local')
        result = client.streamIDAPIs([("Events", 60, False), ("Alarms", 40, True), ("Links", 40, False)])
        print(result)

    def runSubscribe(self):
        client = GrpcClient('localhost', str(Constants.UFM_PLUGIN_PORT), 'local2')
        result = client.subscribeTo('local')
        print(result)


if __name__ == '__main__':
    runner = Runner()
    runner.runStream()
