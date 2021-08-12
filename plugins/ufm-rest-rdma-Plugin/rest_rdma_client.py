import asyncio
import ucp
import numpy as np
import json
import time
import argparse
from enum import Enum

REQUEST_ARGS = ["type", "rest_action", "rest_url", "url_payload", "interface",
                   "username", "password"]

ERROR_RESPOND = '404'
IBDIAGNET_EXCEED_NUMBER_OF_TASKS = "Maximum number of task exceeded, please remove a task before adding a new one"
IBDIAGNET_TASK_ALREDY_EXIST = "Task with same name already exists"
IBDIAGNET_RERROR_RESPONDS = (IBDIAGNET_EXCEED_NUMBER_OF_TASKS, IBDIAGNET_TASK_ALREDY_EXIST)
IBDIAGNET_RESPOSE_DIR = '/tmp/ibdiagnet'    # temporarry - should be received as parameter
                                            # or may be in config file  
                                            # TODO: delete
START_IBDIAG_JOB_URL = "ufmRest/reports/ibdiagnetPeriodic/start/"
GET_IBDIAG_JOB_URL = "ufmRest/reports/ibdiagnetPeriodic/"
base_protocol="https"
port = 13337
n_bytes = 2**30

class actionType(Enum):
    SIMPLE = "simple"
    COMPLICATTED = "complicated"
    IBDIAGNET = "ibdiagnet"
    FILE_TRANSFER = "file_transfer"

def getIbdiagnetJobNameFromPayload(ibdiagnet_payload):
    '''
    return the name of ibdiagned task name - should be supplied by user
    :param ibdiagnet_payload:
    The payload in general:
    '{"general": 
        {"name": "IBDiagnet_CMD_1234567890", 
         "location": "local", 
         "running_mode": "once"}, 
     "command_flags": 
     {"--pc": ""}
     }'
    '''
    try:
        json_request = json.loads(ibdiagnet_payload)
        job_name = str(json_request['general']['name'])
    except ValueError:
        print("ERROR: Decoding ibdiagnet payload JSON has failed")
        return None
    return job_name

def initializeRequestArray(charar, request_arguments):
    '''
    Initialize request array
    :param charar:
    :param request_arguments:
    '''
    charar[0][0] = "Type"
    charar[0][1] = request_arguments['type']
    charar[1][0] = "Action"
    charar[1][1] = request_arguments['rest_action']
    charar[2][0] = "URL"
    charar[2][1] = request_arguments['rest_url']
    charar[3][0] = "Payload"
    charar[3][1] = request_arguments['url_payload']
    charar[4][0] = "Username"
    charar[4][1] = request_arguments['username']
    charar[5][0] = "Password"
    charar[5][1] = request_arguments['password']

def fillArgumentsDict(action_type, rest_action, rest_url, url_payload, username,
                      password):
    '''
    
    :param type:
    :param rest_action:
    :param rest_url:
    :param url_payload:
    :param username:
    :param password:
    '''
    request_arguments = {}
    request_arguments['type'] = action_type
    request_arguments['rest_action'] = rest_action
    request_arguments['rest_url'] = rest_url
    request_arguments['url_payload'] = url_payload
    request_arguments['username'] = username
    request_arguments['password'] = password

    return request_arguments

async def handleComplicatedRespond(ep):
    '''
    Handle complicated rest request and respond
    :param ep: end point
    '''
    pass

async def getIbdiagnetResult(tarball_path):
    '''
    Transfer ibdiagnet result tarball to local server
    :param ep:
    :param tarball_path:
    
    '''
    # first send to server notification that it should be file request
    # send simple request to get status
    print("Create new endpoint")
    end_point = await ucp.create_endpoint(host, port)
    req_charar = np.chararray((6,2), itemsize=200)
    start_file_transf_charar = np.empty_like(req_charar)
    # need to send start first
    ibdiag_request_arguments = fillArgumentsDict(actionType.FILE_TRANSFER.value,
                                                 None, None, None, None, None)
    initializeRequestArray(start_file_transf_charar, ibdiag_request_arguments)
    await end_point.send(start_file_transf_charar)
    data_size = np.empty(1, dtype=np.uint64)
    #file_path= np.chararray((1), itemsize=len(real_path))
    file_path= np.chararray((1), itemsize=200)
    # send message
    file_path[0]=tarball_path
    print("Send File path %s" % file_path[0].decode())
    await end_point.send(file_path)  # send the real message
    print("Receive Data size")
    await end_point.recv(data_size)  # receive the echo
    print("Allocate data for bytes - to receive data %d" % data_size[0])
    resp = bytearray(b"m" * data_size[0])
    # recv response
    print("Receive File")
    resp_data = np.empty_like(resp)
    await end_point.recv(resp_data)  # receive the echo
    receive_location_file = "/".join([IBDIAGNET_RESPOSE_DIR,tarball_path.split('/')[-1]])
    f = open(receive_location_file, "wb")
    f.write(resp_data)

async def handleIbdiagnetRespond(parsed_respond, ibdiag_request_arguments):
    '''
    Handle request respond related to ibdiagnet. including file transfer
    :param ep:
    '''
    # allocation definition of size of data (file that should be received)
    print("Get ibdiagnet session params from payload")
    #----------------------------------------------------------
    job_name = getIbdiagnetJobNameFromPayload(
                                ibdiag_request_arguments.get("url_payload"))
    username = ibdiag_request_arguments.get("username")
    password = ibdiag_request_arguments.get("password")
    #---------------------------------------------------------
    print("Create new endpoint")
    end_point = await ucp.create_endpoint(host, port)
    data_size = np.empty(1, dtype=np.uint64)
    file_path= np.chararray((1), itemsize=200)
    ibdiag_resp_array= np.chararray((1), itemsize=n_bytes) # will get there the response
    # allocation of name of file path to be received - no need to 
    # we will get full respond of data and path will be one of fields - json
    #===========================================================================
    # file_path= np.chararray((1), itemsize=200)
    # real_path="/tmp/history_test_fil.tar.gz"
    #===========================================================================
    # send message
    print("handleIbdiagnetRespond: Receive response for simple request")
    print(json.dumps(parsed_respond, indent=4, sort_keys=True))
    # send simple request to get status
    print("Send start for ibdiagnet task")
    req_charar = np.chararray((6,2), itemsize=200)
    start_charar = np.empty_like(req_charar)
    # need to send start first
    print("Initialize request for start of ibdiagnet")
    ibdiagnet_url = "%s%s" % (START_IBDIAG_JOB_URL, job_name)
    ibdiag_request_arguments = fillArgumentsDict(actionType.SIMPLE.value,
                               "POST", ibdiagnet_url, None, username, password)
    print("Initialize start_charar request for start of ibdiagnet")
    initializeRequestArray(start_charar, ibdiag_request_arguments)
    print(start_charar)
    print("Send ibdiagnet task start")
    await end_point.send(start_charar)
    ibdiag_start_resp = np.empty_like(ibdiag_resp_array)
    await end_point.recv(ibdiag_start_resp)  # receive the echo
    ibdiag_start_as_string=ibdiag_start_resp[0].decode()
    print("On Start action received %s" % ibdiag_start_as_string)
    await end_point.close()
    print("Initialize request for get array")
    ibdiag_start_resp = np.empty_like(ibdiag_resp_array)
    # let's say it was OK - start sending requests if completed
    await end_point.close()
    #time.sleep(15) # -------->>> replace with loop
    # loop to verify if job completed succesfully  
    num_of_retries = 15
    # create a new end_point
    while num_of_retries > 0:
        end_point = await ucp.create_endpoint(host, port)
        get_charar = np.empty_like(req_charar)
        request_url_path = "%s%s" % (GET_IBDIAG_JOB_URL, job_name)
        ibdiag_request_arguments = fillArgumentsDict(actionType.SIMPLE.value,
                        "GET", request_url_path, None, username, password)
        initializeRequestArray(get_charar, ibdiag_request_arguments)
        await end_point.send(get_charar)  # send the real message
        # recv response in different way and handle differently
        print("Receive response for simple request for ibdiagnet")
        ibdiag_resp = np.empty_like(ibdiag_resp_array)
        await end_point.recv(ibdiag_resp)  # receive the echo
        ibdiag_as_string=ibdiag_resp[0].decode()
        try:
            if ibdiag_as_string.startswith(ERROR_RESPOND):
                print("ERROR: Request Failed: %s" % ibdiag_as_string)
                break
            else:
                ibdiag_parsed_respond = json.loads(ibdiag_as_string.strip())
                print(ibdiag_parsed_respond)
                print(json.dumps(ibdiag_parsed_respond, indent=4, sort_keys=True))
                print("Get status")
                task_status = str(ibdiag_parsed_respond["last_run_result"])
                print("Task_status %s" % task_status)
                if task_status != 'Successful':
                    print("Request again")
                    num_of_retries -= 1
                    time.sleep(1)
                else:
                    # take path of tarball file
                    tarball_path = str(ibdiag_parsed_respond["last_result_location"])
                    print("Received tarbalpath %s" % tarball_path)
                    # Test - to remove when move to work ontwo servers
                    test_tb_path = "/opt/ufm/files/periodicIbdiagnet/IBDiagnet_CMD_123456789/IBDiagnet_CMD_123456789-09-08-2021-14.14.14.tgz"
                    tarball_path = test_tb_path # TODO: remove it
                    # -----
                    await end_point.close()
                    await getIbdiagnetResult(tarball_path)
                    break
        except Exception as e:
            print("Error. Failed to get ibdiagnet result file")

async def main():
    parser = createBaseParser()
    allocateRequestArgs(parser)
    arguments = vars(parser.parse_args())
    request_arguments = extractRequestArgs(arguments)
    print("Received arguments: %s" % str(request_arguments))
    global host
    host = ucp.get_address(ifname=request_arguments['interface'])  # ib device name
    print("Create endpoint")
    ep = await ucp.create_endpoint(host, port)
    print("Initialize chararray to sent request to client")
    charar = np.chararray((6,2), itemsize=200)
    resp_array= np.chararray((1), itemsize=n_bytes) #temporarry
    initializeRequestArray(charar, request_arguments)
    # need to separate simple rest requests and more complicated - ibdiagnet related
    # the request and also respond will be different and need to handle it
    print("Send NumPy request char array")
    await ep.send(charar)  # send the real message
    # recv response in different wat and handle differently
    print("Receive response for simple request")
    resp = np.empty_like(resp_array)
    await ep.recv(resp)  # receive the echo
    as_string=resp[0].decode()
    ready_string = as_string.replace("N\\/A", "NA")
    # Check if respond was OK. If not - print error
    try:
        if ready_string.startswith(ERROR_RESPOND):
            print("Request Failed: %s" % ready_string)
            await ep.close()
            return
        else:
            if (request_arguments['type'] == actionType.IBDIAGNET.value and
                ready_string in IBDIAGNET_RERROR_RESPONDS):
                print("%s" % ready_string)
                await ep.close()
                return
            parsed_respond = json.loads(ready_string.strip())
    except:
        print("Got respond: %s" % ready_string)
    if request_arguments['type'] == actionType.IBDIAGNET.value:
        await ep.close() # close old ep - will need to crate  a new one
        # need to get from respond the name of ibdiagnet job
        await handleIbdiagnetRespond(parsed_respond, request_arguments)
    elif request_arguments['type'] == actionType.COMPLICATTED.value:
        await handleComplicatedRespond(parsed_respond)
    else:
        print(json.dumps(parsed_respond, indent=4, sort_keys=True))
    await ep.close()

def createBaseParser():
    """
    Create an argument parser
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    return parser

def allocateRequestArgs(parser):
    '''
    Definition of arguments
    :param parser:
    '''
    request = parser.add_argument_group('request')
    request.add_argument("-i", "--interface", action="store",
                            required=True, default="ib0",
                            choices=None, help="Connection interface name")
    request.add_argument("-u", "--username", action="store",
                                required=False, default="admin", choices=None,
                                help="UFM REST request user name")
    request.add_argument("-p", "--password", action="store",
                            required=False, default="123456", choices=None,
                            help="UFM REST password")
    request.add_argument("-t", "--type", action="store",
                            required=True, default="simple",
                            choices=["simple", "complicated", "ibdiagnet"],
                            help="Action type to be performed")
    request.add_argument("-a", "--rest_action", action="store",
                            required=True, default="GET", choices=["GET", "PUT", "SET", "POST"],
                            help="REST Action to perform")
    request.add_argument("-w", "--rest_url", action="store",
                            required=True, default=None, choices=None,
                            help="UFM REST URL")
    request.add_argument("-l", "--url_payload", action="store",
                            default=None, required=None,
                            choices=None,
                            help="REST payload")


def extractRequestArgs(arguments):
        """
        Extracting the connection arguments from the parsed arguments.
        """
        return dict([(arg, arguments.pop(arg))
                     for arg in REQUEST_ARGS])
        

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
