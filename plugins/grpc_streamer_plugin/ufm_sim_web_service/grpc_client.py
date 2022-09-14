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
from plugins.grpc_streamer_plugin.ufm_sim_web_service.GRPCMessageConverter import encode_destination, decode_destination,decode_message
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Destination import Destination
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Config import Constants


class GrpcClient:

    def __init__(self, server_ip, server_port,job_id):
        self.grpc_channel = f'{server_ip}:{server_port}'
        self.job_id = job_id

    def _add_session(self,username,password):
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

    def _added_job(self, api_list):
        self.dest = Destination(self.job_id, api_list, None, None)
        try:
            self.channel = grpc.insecure_channel(self.grpc_channel)
            self.stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(self.channel)
            self.stub.CreateSession(grpc_plugin_streamer_pb2.SessionAuth(client_user=self.job_id,username="admin",
                                                                         password="123456"))
            self.stub.AddDestination(self.dest.to_message())
            self.channel.close()
        except grpc.RpcError as e:
            return False
        return True

    def onceApis(self,api_list):
        success = self._added_job(api_list)
        if not success:
            return None
        try:
            self.channel = grpc.insecure_channel(self.grpc_channel)
            self.stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(self.channel)
            result = self.stub.RunOnceJob(grpc_plugin_streamer_pb2.gRPCStreamerID(job_id=self.job_id))
            self.channel.close()
            return result
        except grpc.RpcError as e:
            return None

    def preiodicallyApis(self, api_list):
        success = self._added_job(api_list)
        if not success:
            return None
        try:
            self.channel = grpc.insecure_channel(self.grpc_channel)
            self.stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(self.channel)
            interator = self.stub.RunStreamJob(grpc_plugin_streamer_pb2.gRPCStreamerID(job_id=self.job_id))
            result_list = []
            for x in interator:
                print(x.job_id)
                result_list.append(x)

            self.channel.close()
            return result_list
        except grpc.RpcError as e:
            print(f"client couldnt get stream: {e}")
            return None

    def subscribeTo(self, ip):

        message = grpc_plugin_streamer_pb2.gRPCStreamerID(job_id=ip)
        try:
            self.channel = grpc.insecure_channel(self.grpc_channel)
            self.stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(self.channel)
            interator = self.stub.SubscribeToStream(message)
            result_list = []
            for x in interator:
                print(x)
                result_list.append(x)

            self.channel.close()
            return result_list
        #except _InactiveRpcError
        except grpc.RpcError as e:
            print(f"client couldnt connect: {e}")
            return False

def run():
    #    with gNMIclient(target=('localhost','8002'), insecure=True) as gc:
    #        print(gc.connect())

    client = GrpcClient('localhost', str(Constants.UFM_PLUGIN_PORT), 'local')
    result = client.onceApis([("Events", 10, True), ("Alarms", 10, True), ("Links", 40, False), ("stuff")])
    print(result)


def run2():
    client = GrpcClient('localhost', str(Constants.UFM_PLUGIN_PORT), 'local')
    result = client.preiodicallyApis([("Events", 60, False), ("Alarms", 40, True), ("Links", 40, False)])
    print(result)

def run3():
    client = GrpcClient('localhost', str(Constants.UFM_PLUGIN_PORT), 'local2')
    result = client.subscribeTo('local')
    print(result)

if __name__ == '__main__':
   run()