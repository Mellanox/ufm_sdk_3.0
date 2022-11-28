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
        print("Error occurred while importing python modules, Cannot use get command"
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, Cannot use get command"
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


COMMANDS = {'get': ['events', 'alarms', 'links', 'jobs'],
            'client': ['once', 'stream', 'subscribe', 'session', 'create', 'once_id', 'stream_id'],
            'server': ['up', 'subscribers', 'down'],
            'port': [],'exit':[]}
BOLD = '\033[1m'
BOLD_END = '\033[0;0m'


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
        self.grpc_port = Constants.UFM_PLUGIN_PORT

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
        client = GrpcClient(server_ip, self.grpc_port, id)
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
        #['up', 'subscribers', 'down']
        try:
            if action=='up':
                self.server = grpc_server.GRPCPluginStreamerServer(ufm_ip)
                self.server.start()
                return
            if action == 'down':
                self.server.stop()
                return
            if action == 'subscribers':
                if ufm_ip is None:
                    if self.server is None:
                        print("Server is not up in console, use argument --server_ip=server_ip for "
                              "list of subscribers in the grpc server")
                        return
                    print(self.server.subscribers)
                    return
                print(GrpcClient(ufm_ip,self.grpc_port,"list").subscriberList())
        except Exception as e:
            print(e)

    def change_port(self,new_port):
        try:
            self.grpc_port = int(new_port)
        except ValueError as e:
            print(e)
            print("write the number of port you want, for example:"
                  " port 8004")

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
    print(f"can only use {len(COMMANDS)} main commands: {list(COMMANDS.keys())}\n\n"
          f"{BOLD}port{BOLD_END} command change the port the console is listening to grpc,\n"
          f"The default port is {Constants.UFM_PLUGIN_PORT}, and it is on the server as well\n"
          f"port <number_grpc_port>\n\n"
          f"{BOLD}get{BOLD_END} command can get from rest api from machine, need what rest api choosing from {COMMANDS['get']}\n"
          f"also needs ufm ip and and auth. for example this is a correct get command\n"
          f"get events --host=localhost --auth=username,password\n\n"
          f"{BOLD}server{BOLD_END} command manage a grpc server. need an action choosing from {COMMANDS['server']}\n"
          f"if using up also need ufm ip to create it. for example\nserver up --ufm_ip=localhost\nserver subscribers\n\n"
          f"{BOLD}client{BOLD_END} command create client to connect to the server using any of those actions {COMMANDS['client']}.\n"
          f"to get information from grpc server one need to create session>subscribe> once/stream with id.\n"
          f"or you can create a once/stream request with once/stream and provide all.\n"
          f"or there is possibility to subscribe to subscriber stream with given id.\n"
          f"examples :\n"
          f"client session --server_ip=localhost --id=client1 --auth=username,password --token=token\n"
          f"client create --server_ip=localhost --id=client1 --apis=events,links,alarms\n"
          f"client once_id --server_ip=localhost --id=client1\n"
          f"client stream --server_ip=localhost --id=client2 --auth=username,password --apis=events;40;True,links;20;False,alarms;10\n"
          f"client subscribe --server_ip=localhost --id=client1")
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
        main_function = parts[0]
        if main_function == 'port':
            if len(parts)==2:
                user.change_port(parts[1])
            command = input("enter command:") if len(parts)==2 else print_usage()
            continue

        if len(parts) < 2 or main_function not in COMMANDS.keys() or parts[1] not in COMMANDS[main_function]:
            command = print_usage()
            continue
        try:
            args = process_args(parts[2:])
            if main_function == 'server':
                user.server_action(args[0], parts[1])
            elif main_function == 'get':
                user.get_request(host=args[0], auth=args[2], what_to_bring=parts[1],token=args[4])
            elif main_function == 'client':
                user.client_actions(server_ip=args[0], action=parts[1], id=args[1], api_list=args[3], auth=args[2], token=args[4])
        except Exception as e:
            print(e)

        command = input("enter command:")

    logger.log.close()

if __name__ == '__main__':
    main()