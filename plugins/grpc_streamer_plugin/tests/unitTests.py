import unittest
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_server as server
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_client as client
import grpc
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2_grpc as grpc_plugin_streamer_pb2_grpc
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Destination import Destination
from google.protobuf.empty_pb2 import Empty
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Config import Constants

class TestPluginStreamer(unittest.TestCase):
    def setUp(self):
        self.job_id = 'coco'
        self._server = server.GRPCPluginStreamerServer('localhost')
        self._server.start()
        self._client = client.GrpcClient('localhost', Constants.UFM_PLUGIN_PORT, self.job_id)

    def tearDown(self):
        self._server.stop()

    def testAddSession(self):
        result = self._client._add_session('admin','123456')
        self.assertTrue(result)

    def testAddUser(self):
        result = self._client._added_job([('Events')])
        self.assertTrue(result)
        self.assertTrue(len(self._server.destinations) == 1)
        try:
            channel = grpc.insecure_channel(f'localhost:{Constants.UFM_PLUGIN_PORT}')
            stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(channel)
            result = stub.ListDestinations(Empty())
            self.assertTrue(isinstance(result,grpc_plugin_streamer_pb2.ListDestinationParams))
            self.assertTrue(len(result.destinations)==1)
        except grpc.RpcError as e:
            print("Couldnt add a session")
            self.assertTrue(False, e)

    def testGetOnce(self):
        result = self._client.onceApis([('Events'), ("Alarms")])
        self.assertIsNotNone(result)

    def testAddWithoutSession(self):
        dest = Destination(self.job_id, [('Events'), ("Alarms")], None, None)
        try:
            channel = grpc.insecure_channel(f'localhost:{Constants.UFM_PLUGIN_PORT}')
            stub = grpc_plugin_streamer_pb2_grpc.GeneralGRPCStreamerServiceStub(channel)
            result = stub.AddDestination(dest.to_message())
            channel.close()
            self.assertTrue(isinstance(result,grpc_plugin_streamer_pb2.SessionRespond))
            self.assertTrue(result.respond == Constants.LOG_CANNOT_DESTINATION + Constants.LOG_CANNOT_NO_SESSION)
            self.assertTrue(len(self._server.destinations) == 0)
        except grpc.RpcError as e:
            self.assertFalse(True,e)

    def testEmptyDestination(self):
        try:
            self._client.onceApis(['junk'])
        except Exception as e:
            self.assertEqual(str(e),Constants.LOG_NO_REST_DESTINATION)

    def testAllTaskAreRestCalls(self):
        result = self._client.onceApis([('Events'), ("junk")])
        for message in result.results:
            self.assertEqual(message.task_name, 'Events')


def suiteMaking():
    suite = unittest.TestSuite()
    suite.addTest(TestPluginStreamer('testAddSession'))
    suite.addTest(TestPluginStreamer('testAddUser'))
    suite.addTest(TestPluginStreamer('testGetOnce'))
    suite.addTest(TestPluginStreamer('testAddWithoutSession'))
    suite.addTest(TestPluginStreamer('testEmptyDestination'))
    suite.addTest(TestPluginStreamer('testAllTaskAreRestCalls'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suiteMaking())
