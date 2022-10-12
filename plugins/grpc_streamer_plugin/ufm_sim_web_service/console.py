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
import sys,os,platform

import grpc_server
from grpc_client import GrpcClient
from Config import Constants
try:
    from utils import ufm_rest_client
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


commands = {'get': ['events', 'alarms', 'links', 'jobs'],
            'client': ['once', 'stream', 'subscribe', 'session', 'create', 'once_id', 'stream_id'],
            'server': ['up', 'destinations', 'down']}


class UserActions:
    def __init__(self):
        self._dictCalls = {'logic': "/resources/logical_servers",
                           'telemetry': "/monitoring/aggr_topx?object=servers&attr=bw",
                           'network': "/app/network_views",
                           'events': "/app/events",
                           'alarms': "/app/alarms",
                           'links': "/resources/links",
                           'jobs': "/jobs",
                           'system': "/resources/systems"}
    def get_request(self,what_to_bring,host,auth,token):
        if auth is None: auth=[None,None]
        user=ufm_rest_client.UfmRestClient(host,"https",token,"ufmRest"+("V3" if token else ""),auth[0],auth[1])
        result = user.send_request(self._dictCalls[what_to_bring])
        if result is None or result.status_code!=200:
            print(result)
        else:
            print(result.json())


    def client_actions(self,server_ip, action, id, api_list, auth, token):
        #['once', 'stream', 'subscribe', 'session', 'create', 'once_id', 'stream_id']
        if server_ip is None or id is None:
            print("Need server ip and id to continue")
            return

        respond = ''
        client = GrpcClient(server_ip, Constants.UFM_PLUGIN_PORT, id)
        if action == 'session':
            if auth is None:
                auth = [None, None]
            respond = client.add_session(auth[0], auth[1], token)
        elif action == 'create':
            respond = client.added_job(api_list)
        elif action == 'subscribe':
            respond = client.subscribeTo(id)
        elif action == 'once_id':
            respond = client.onceIDApis(api_list, auth,token)
        elif action == 'stream_id':
            respond = client.streamIDAPIs(api_list, auth,token)
        elif action == 'once':
            respond = client.onceApis(api_list, (token if token else auth))
        elif action == 'stream':
            respond = client.streamApis(api_list, (token if token else auth))
        print(respond)
        return respond

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
                print(self.server.subscribers)
                return
        except Exception as e:
            print(e)

class Logger:
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("grpc_streamer_console.log", "w")

    def write(self,message):
        self.log.write(message)
        self.terminal.write(message)

    def flush(self):
        self.log.flush()
        self.terminal.flush()

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
    print("client session --server_ip=localhost --id=client1 --auth=username,password --token=token")
    print("client create --server_ip=localhost --id=client1 --apis=events,links,alarms")
    print("client once_id --server_ip=localhost --id=client1")
    print("client stream --server_ip=localhost --id=client2 --auth=username,password --apis=events;40;True,links;20;False,alarms;10")
    print("client subscribe --server_ip=localhost --id=client1")
    command = input("enter command:")
    return command


def process_args(command_list):
    ufm_ip, job_id, auth, apis, token = None, None, None, None, None
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
            apis = [pairs.split(';') for pairs in value.split(',')]
        elif key == 'token':
            token = value

    return ufm_ip, job_id, auth, apis, token


def main():
    logger = Logger()
    sys.stdout = logger
    command = input("enter command:")

    user = UserActions()
    while command != 'exit':
        print(">>" + command)
        parts = ' '.join(command.split()).split(' ')
        if len(parts) < 2 or parts[0] not in commands.keys() or parts[1] not in commands[parts[0]]:
            command = print_usage()
            continue
        try:
            args = process_args(parts[2:])
            if parts[0] == 'server':
                user.server_action(args[0], parts[1])
            elif parts[0] == 'get':
                user.get_request(host=args[0], auth=args[2], what_to_bring=parts[1],token=args[4])
            elif parts[0] == 'client':
                user.client_actions(server_ip=args[0], action=parts[1], id=args[1], api_list=args[3], auth=args[2], token=args[4])
        except Exception as e:
            print(e)

        command = input("enter command:")

    logger.log.close()

if __name__ == '__main__':
    main()