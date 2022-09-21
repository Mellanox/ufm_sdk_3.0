import grpc_server
from grpc_client import GrpcClient
import requests
import grpc
from Config import Constants
import grpc_plugin_streamer_pb2
import grpc_plugin_streamer_pb2_grpc
from Destination import Destination


class RestClient:
    def __init__(self,host,auth,port):
        self._dictCalls = {'logic': "/ufmRest/resources/logical_servers",
                        'telemetry': "/ufmRest/monitoring/aggr_topx?object=servers&attr=bw",
                        'network': "/ufmRest/app/network_views",
                        'events': "/ufmRest/app/events",
                        'alarms': "/ufmRest/app/alarms",
                        'links': "/ufmRest/app/links",
                        'jobs': "/ufmRest/app/jobs",
                        'system': "/ufmRest/resources/systems"}

        self._session = requests.Session()
        self._session.auth = auth
        self._session.verify = False
        self._session.headers.update({'Content-Type': 'application/json; charset=utf-8'})

        self._host = host
        self._port = port  # web

    def send_get_request(self, key):
        if key not in self._dictCalls:
            print("only those keys are available:" +str(self._dictCalls.keys()))
            return None
        resource_path = self._dictCalls[key]
        if ':' in self._host:
            url = 'https://[{0}]{1}'.format(self._host, resource_path)
        else:
            url = 'https://{0}{1}'.format(self._host, resource_path)
        try:
            respond = self._session.get(url)
            return respond
        except requests.ConnectionError as e:
            print("Wasn't able to reach "+resource_path+". Connection Error, please see this exception.\n"+str(e))
        except requests.Timeout as e:
            print("Wasn't able to reach " + resource_path + ". Timeout Error, please see this exception.\n" + str(e))
        except requests.RequestException as e:
            print("Wasn't able to reach " + resource_path + ". Request Error, please see this exception.\n" + str(e))
        except KeyboardInterrupt as e:
            print("Wasn't able to reach " + resource_path + ". Connection Error, please see this exception.\n" + str(e))
        return None


commands = {'get': ['events', 'alarms', 'links', 'jobs'],
            'client': ['once', 'stream', 'subscribe', 'session', 'create', 'once_id', 'stream_id'],
            'server': ['up', 'destinations', 'down']}


class UserActions:
    def get_request(self,what_to_bring,host,auth):
        self.rest_client = RestClient(host,auth,443)
        result = self.rest_client.send_get_request(what_to_bring)
        if result is None or result.status_code!=200:
            print(result)
        else:
            print(result.json())


    def client_actions(self,server_ip, action, id, api_list, auth):
        #['once', 'stream', 'subscribe', 'session', 'create', 'once_id', 'stream_id']

        respond = ''
        client = GrpcClient(server_ip, Constants.UFM_PLUGIN_PORT, id)
        if action == 'session':
            respond = client.add_session(auth[0],auth[1])
        elif action == 'create':
            respond = client.added_job(api_list)
        elif action == 'subscribe':
            respond = client.subscribeTo(id)
        elif action == 'once_id':
            respond=client.onceIDApis(api_list, auth, True)
        elif action == 'stream_id':
            respond = client.streamIDAPIs(api_list, auth, True)
        elif action == 'once':
            respond = client.onceApis(api_list, auth)
        elif action == 'stream':
            respond = client.streamApis(api_list, auth)

        print(respond)

    def server_action(self, ufm_ip, action):
        #['up', 'destinations', 'down']
        try:
            if action=='up':
                self.server = grpc_server.GRPCPluginStreamerServer(ufm_ip)
                self.server.start()
                return
            elif action == 'down':
                self.server.stop()
                return
            elif action == 'destinations':
                print(self.server.destinations)
                return
        except Exception as e:
            print(e)


def print_usage():
    print(f"can only use {len(commands)} main commands: {list(commands.keys())}\n")
    print(f"get command can get from rest api from machine, need what rest api choosing from {commands['get']}")
    print("also needs ufm ip and and auth. for example this is a correct get command")
    print("get events --host=localhost --auth=username,password\n")
    print(f"server command manage a grpc server. need an action choosing from {commands['server']}")
    print('if using up also need ufm ip to create it. for example')
    print("server up --ufm_ip=localhost")
    print("server destinations\n")
    print(f"client command create client to connect to the server using any of those actions {commands['client']}.")
    print('to get information from grpc server one need to create session>destination> once/stream with id.')
    print("or you can create a once/stream request with once/stream and provide all.")
    print("or there is possibility to subscribe to destination stream with given id.")
    print("examples :")
    print("client session --server_ip=localhost --id=client1 --auth=username,password")
    print("client create --server_ip=localhost --id=client1 --apis=events,links,alarms")
    print("client once_id --server_ip=localhost --id=client1")
    print("client stream --server_ip=localhost --id=client2 --auth=username,password --apis=events,links,alarms")
    print("client subscribe --server_ip=localhost --id=client1")


def process_args(command_list):
    ufm_ip, job_id, auth, apis = None, None, None, None
    for arg in command_list:
        if not arg.startswith('--'): continue
        key, value = arg[2:].split('=')
        if key in ['server_ip', 'ufm_ip', 'host']:
            ufm_ip = value
        elif key == 'id':
            job_id = value
        elif key == 'auth':
            auth = tuple(value.split(','))
        elif key == 'apis':
            apis = value.split(',')

    return ufm_ip, job_id, auth, apis


if __name__ == '__main__':
    command = input("enter command:")
    user=UserActions()
    while command != 'exit':
        parts = ' '.join(command.split()).split(' ')
        if len(parts)<2 or parts[0] not in commands.keys() or parts[1] not in commands[parts[0]]:
            print_usage()
            command = input("enter command:")
            continue
        try:
            args = process_args(parts[2:])
            if parts[0] == 'server':
                user.server_action(args[0],parts[1])
            elif parts[0] == 'get':
                user.get_request(host=args[0],auth=args[2],what_to_bring=parts[1])
            elif parts[0] == 'client':
                user.client_actions(server_ip=args[0],action=parts[1],id=args[1],api_list=args[3],auth=args[2])
        except Exception as e:
            print(e)
        command = input("enter command:")

