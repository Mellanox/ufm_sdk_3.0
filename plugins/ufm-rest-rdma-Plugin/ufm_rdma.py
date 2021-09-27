import asyncio
import ucp
import numpy as np
import ctypes
import sys
import os
import configparser
import requests
from ucp._libs.utils_test import (
    blocking_flush,
    get_endpoint_error_handling_default,
)
from ucp._libs.arr import Array
import json
import time
import logging
import argparse
import struct
from enum import Enum

SERVICE_NAME = b"ufm_rest_service"
DEFAULT_CONFIG_FILE_NAME = "ufm_rdma.ini"
DEFAULT_LOG_FILE_NAME = "ufm_rdma.log"
DEFAULT_HOST_NAME = "localhost"
WORKING_DIR_NAME = os.path.dirname(os.path.realpath(__file__))
SR_LIB_NAME = "libservice_record_wrapper.so"
SR_LIB_PATH = os.path.join(WORKING_DIR_NAME, SR_LIB_NAME)
LOG_FILE_PATH = os.path.join(WORKING_DIR_NAME, DEFAULT_LOG_FILE_NAME)
LOG_FILE_PATH = "/tmp/at_log.log"
SUCCESS_REST_CODE = (200, 201, 202, 203, 204)
ERROR_REST_CODE = (500, 501, 502, 503, 504, 505)
ADDRESS_SR_HOLDER_SIZE = 56
GENERAL_ERROR_NUM = 500
GENERAL_ERROR_MSG = "REST RDMA server failed to send request to UFM Server. Check log file for details"
# load the service record lib
try:
    # sr_lib = ctypes.CDLL('/.autodirect/mtrswgwork/atabachnik/workspace/github/Collectx_master_libsr/src/service_record/libservice_record_wrapper.so')
    sr_lib = ctypes.CDLL(SR_LIB_PATH)
except Exception as e:
    error_message = "Failed to load SR lib: %s" % e
    sys.exit(error_message)

sr_context = ctypes.c_void_p

# sr_wrapper_ctx_t* sr_wrapper_create(const char* service_name, const char* dev_name, int port);
# Function returns
sr_lib.sr_wrapper_create.restype = ctypes.c_void_p
# Function gets arguments
sr_lib.sr_wrapper_create.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]

# bool sr_wrapper_destroy(sr_wrapper_ctx_t* ctx);
# Function returns
sr_lib.sr_wrapper_destroy.restype = ctypes.c_bool
# Function gets arguments
sr_lib.sr_wrapper_destroy.argtypes = [ctypes.c_void_p]

# bool sr_wrapper_register(sr_wrapper_ctx_t* ctx, const void* addr, size_t addr_size);
# Function returns
sr_lib.sr_wrapper_register.restype = ctypes.c_bool
# Function gets arguments
sr_lib.sr_wrapper_register.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]

# bool sr_wrapper_unregister(sr_wrapper_ctx_t* ctx);
# Function returns
sr_lib.sr_wrapper_unregister.restype = ctypes.c_bool
# Function gets arguments
sr_lib.sr_wrapper_unregister.argtypes = [ctypes.c_void_p]

# size_t sr_wrapper_query(sr_wrapper_ctx_t* ctx, void* addr, size_t addr_size);
# Function returns
sr_lib.sr_wrapper_query.restype = ctypes.c_size_t
# Function gets arguments
sr_lib.sr_wrapper_query.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]

# ---------------------------------------------------------------------------------
REQUEST_ARGS = ["type", "rest_action", "ufm_server_ip", "run_mode", "rest_url", "url_payload", "interface",
                "username", "password", "config_file"]

ERROR_RESPOND = '404'
IBDIAGNET_EXCEED_NUMBER_OF_TASKS = "Maximum number of task exceeded, please remove a task before adding a new one"
IBDIAGNET_TASK_ALREDY_EXIST = "Task with same name already exists"
IBDIAGNET_RERROR_RESPONDS = (IBDIAGNET_EXCEED_NUMBER_OF_TASKS, IBDIAGNET_TASK_ALREDY_EXIST)
DEFAULT_IBDIAGNET_RESPONSE_DIR = '/tmp/ibdiagnet'  # temporarry - should be received as parameter
# or may be in config file
# TODO: delete
START_IBDIAG_JOB_URL = "ufmRest/reports/ibdiagnetPeriodic/start/"
GET_IBDIAG_JOB_URL = "ufmRest/reports/ibdiagnetPeriodic/"
base_protocol = "https"
SERVER_MODE_RUN = "server"
CLIENT_MODE_RUN = "client"

N_BYTES = 2 ** 29


class ActionType(Enum):
    SIMPLE = "simple"
    COMPLICATED = "complicated"
    IBDIAGNET = "ibdiagnet"
    FILE_TRANSFER = "file_transfer"
    ABORT = "abort"


class UFMRestAction(Enum):
    GET = "GET"
    PUT = "PUT"
    SET = "SET"
    POST = "POST"


def get_ibdiagnet_job_name_from_payload(ibdiagnet_payload):
    """
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
    """
    try:
        json_request = json.loads(ibdiagnet_payload)
        job_name = str(json_request['general']['name'])
    except ValueError:
        logging.debug("Client: ERROR: Decoding ibdiagnet payload JSON has failed")
        return None
    return job_name


def initialize_request_array(charar, request_arguments):
    """
    Initialize request array
    :param charar:
    :param request_arguments:
    """
    # print(request_arguments) # TODO: delete - for debugging
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
    charar[6][0] = "Host"
    charar[6][1] = request_arguments['ufm_server_ip']


def fill_arguments_dict(action_type, rest_action, rest_url, url_payload, username,
                        password, host):
    """
    Fill arguments dictionary with parameters
    :param action_type:
    :param rest_action:
    :param rest_url:
    :param url_payload:
    :param username:
    :param password:
    :param host:
    """
    request_arguments = {}
    request_arguments['type'] = action_type
    request_arguments['rest_action'] = rest_action
    request_arguments['rest_url'] = rest_url
    request_arguments['url_payload'] = url_payload
    request_arguments['ufm_server_ip'] = host
    request_arguments['username'] = username
    request_arguments['password'] = password

    return request_arguments


async def handle_complicated_respond(ep):
    """
    Handle complicated rest request and respond
    :param ep: end point
    """
    pass


async def get_ibdiagnet_result(end_point, recv_tag, send_tag, tarball_path):
    """
    Transfer ibdiagnet result tarball to local server
    :param end_point: end point
    :param recv_tag: receive tag
    :param send_tag: send tag
    :param tarball_path:
    """
    # first send to server notification that it should be file request
    # send simple request to get status
    req_charar = np.chararray((7, 2), itemsize=200)
    start_file_transf_charar = np.empty_like(req_charar)
    # need to send start first
    ibdiag_request_arguments = fill_arguments_dict(ActionType.FILE_TRANSFER.value,
                                                   None, None, None, None, None, None)
    initialize_request_array(start_file_transf_charar, ibdiag_request_arguments)
    await end_point.send(start_file_transf_charar, tag=send_tag, force_tag=True)
    data_size = np.empty(1, dtype=np.uint64)
    # file_path= np.chararray((1), itemsize=len(real_path))
    file_path = np.chararray((1), itemsize=200)
    # send message
    file_path[0] = tarball_path
    logging.debug("Client: Send File path %s" % file_path[0].decode())
    await end_point.send(file_path, tag=send_tag, force_tag=True)  # send the real message
    logging.debug("Client: Receive Data size")
    await end_point.recv(data_size, tag=recv_tag, force_tag=True)  # receive the echo
    logging.debug("Client: Allocate data for bytes - to receive data %d" % data_size[0])
    if data_size == 0:  # failure on file receive on server side
        await cancel_ibdiagnet_respond(end_point, send_tag)
        error_msg = "Failed to get file %s on server side" % tarball_path
        logging.error(error_msg)
        return
    resp = bytearray(b"m" * data_size[0])
    # recv response
    logging.debug("Client: Receive ibdiagnet tar File")
    resp_data = np.empty_like(resp)
    await end_point.recv(resp_data, tag=recv_tag, force_tag=True)  # receive the echo
    ibdiagnet_resp_dir = rdmaRestConfig.get("Client", "ibdiagnet_file_location_dir",
                                            fallback=DEFAULT_IBDIAGNET_RESPONSE_DIR)
    # ibdiagnet_resp_dir = DEFAULT_IBDIAGNET_RESPONSE_DIR
    if not os.path.exists(ibdiagnet_resp_dir):  # create if not exist
        os.makedirs(ibdiagnet_resp_dir)
    receive_location_file = "/".join([ibdiagnet_resp_dir,
                                      tarball_path.split('/')[-1]])
    f = open(receive_location_file, "wb")
    f.write(resp_data)
    print("Ibdiagnet output file stored at %s" % receive_location_file)


async def cancel_complicated_respond(end_point):
    """
    :param end_point:
    """
    pass


async def cancel_ibdiagnet_respond(end_point, send_tag):
    """
    :param end_point:
    :param send_tag:
    """
    logging.debug("Client: cancelIbdiagnetRespond: Send abort to server")
    req_charar = np.chararray((7, 2), itemsize=200)
    abort_charar = np.empty_like(req_charar)

    ibdiag_request_arguments = fill_arguments_dict(ActionType.ABORT.value,
                                                   None, None, None, None, None, None)
    initialize_request_array(abort_charar, ibdiag_request_arguments)
    await end_point.send(abort_charar, tag=send_tag, force_tag=True)


async def handle_ibdiagnet_respond(end_point, recv_tag, send_tag, parsed_respond, ibdiag_request_arguments):
    """
    Handle request respond related to ibdiagnet. including file transfer
    :param end_point: end point
    :param recv_tag: receive tag
    :param send_tag: send tag
    :param parsed_respond:
    :param ibdiag_request_arguments:
    """
    global rdmaRestConfig
    # allocation definition of size of data (file that should be received)
    job_name = get_ibdiagnet_job_name_from_payload(
        ibdiag_request_arguments.get("url_payload"))
    host = ibdiag_request_arguments.get("host")
    username = ibdiag_request_arguments.get("username")
    password = ibdiag_request_arguments.get("password")
    # ---------------------------------------------------------
    data_size = np.empty(1, dtype=np.uint64)
    file_path = np.chararray((1), itemsize=200)
    ibdiag_resp_array = np.chararray((2), itemsize=N_BYTES)  # will get there the response
    # allocation of name of file path to be received - no need to 
    # we will get full respond of data and path will be one of fields - json
    logging.debug("Client: handleIbdiagnetRespond: Receive response for simple request")
    # print(json.dumps(parsed_respond, indent=4, sort_keys=True))
    # send simple request to get status
    logging.debug("Client: Send start for ibdiagnet task")
    req_charar = np.chararray((7, 2), itemsize=200)
    start_charar = np.empty_like(req_charar)
    # need to send start first
    ibdiagnet_url = "%s%s" % (START_IBDIAG_JOB_URL, job_name)
    ibdiag_request_arguments = fill_arguments_dict(ActionType.IBDIAGNET.value,
                                                   "POST", ibdiagnet_url, None, username, password, host)
    initialize_request_array(start_charar, ibdiag_request_arguments)
    # print(start_charar)
    await end_point.send(start_charar, tag=send_tag, force_tag=True)
    ibdiag_start_resp = np.empty_like(ibdiag_resp_array)
    await end_point.recv(ibdiag_start_resp, tag=recv_tag, force_tag=True)  # receive the echo
    if int(ibdiag_start_resp[0]) not in SUCCESS_REST_CODE:
        ibdiag_start_failure_as_string = ibdiag_start_resp[1].decode()
        logging.error("Client: Failed to start ibdiagnet task: %s" %
                      ibdiag_start_failure_as_string)
        await cancel_ibdiagnet_respond(end_point, send_tag)
        return
    ibdiag_start_as_string = ibdiag_start_resp[1].decode()
    logging.debug("Client: On Start action received %s" % ibdiag_start_as_string)
    logging.debug("Client: Initialize request for get array")
    ibdiag_start_resp = np.empty_like(ibdiag_resp_array)
    # let's say it was OK - start sending requests if completed
    # loop to verify if job completed succesfully  
    num_of_retries = int(rdmaRestConfig.get("Client", "ibdiagnet_wait_intetrval",
                                            fallback=300))
    # create a new end_point
    while num_of_retries > 0:
        get_charar = np.empty_like(req_charar)
        request_url_path = "%s%s" % (GET_IBDIAG_JOB_URL, job_name)
        ibdiag_request_arguments = fill_arguments_dict(ActionType.IBDIAGNET.value,
                                                       "GET", request_url_path, None, username, password, host)
        initialize_request_array(get_charar, ibdiag_request_arguments)
        await end_point.send(get_charar, tag=send_tag, force_tag=True)  # send the real message
        # recv response in different way and handle differently
        logging.debug("Client: Receive response for simple request for ibdiagnet")
        ibdiag_resp = np.empty_like(ibdiag_resp_array)
        await end_point.recv(ibdiag_resp, tag=recv_tag, force_tag=True)  # receive the echo
        request_status = int(ibdiag_resp[0])
        ibdiag_as_string = ibdiag_resp[1].decode()
        try:
            # if ibdiag_as_string.startswith(ERROR_RESPOND):
            if request_status not in SUCCESS_REST_CODE:
                logging.error("Client: Request Failed: %s" % ibdiag_as_string)
                break
            else:
                ibdiag_parsed_respond = json.loads(ibdiag_as_string.strip())
                # print(ibdiag_parsed_respond)
                # print(json.dumps(ibdiag_parsed_respond, indent=4, sort_keys=True))
                task_status = str(ibdiag_parsed_respond["last_run_result"])
                logging.debug("Client: Task status %s" % task_status)
                if task_status != 'Successful':
                    logging.debug("Client: Request again")
                    num_of_retries -= 1
                    time.sleep(1)
                else:
                    # take path of tarball file
                    tarball_path = str(ibdiag_parsed_respond["last_result_location"])
                    logging.debug("Client: Received tarballpath %s" % tarball_path)
                    # -----
                    await get_ibdiagnet_result(end_point, recv_tag, send_tag, tarball_path)
                    break
        except Exception as e:
            logging.error("Client: Error. Failed to get ibdiagnet result file %s" % e)


def register_local_address_in_service_record(interface):
    """
    Register local address in service record
    :param interface: - interface, e.g., mlx5_0
    """
    address = ucp.get_worker_address()
    serialized_address = bytearray(address)
    # print(serialized_address)
    addres_value_len = len(serialized_address)
    # print("addres_value_len %d" % addres_value_len)
    address_value_to_send = (ctypes.c_char * addres_value_len).from_buffer(
        serialized_address)
    # publish local address to server record
    sr_service_name = ctypes.c_char_p(SERVICE_NAME)
    sr_device_name = ctypes.c_char_p(str.encode(interface))
    sr_context = sr_lib.sr_wrapper_create(sr_service_name, sr_device_name, 1)
    if not sr_context:
        logging.critical("Server: Unable to allocate sr_wrapper_ctx_t")
        return 1
    else:
        logging.debug("Server: sr_wrapper_ctx_t init done")
    if not sr_lib.sr_wrapper_register(sr_context, address_value_to_send,
                                      addres_value_len):
        logging.critical("Server: Unable to register sr_wrapper")
        return 1


async def receive_rest_request(end_point, recv_tag):
    """
    Handle simple rest request
    :param end_point: - end point
    :param recv_tag: - receive tag
    """
    arr = np.chararray((7, 2), itemsize=200)
    await end_point.recv(arr, tag=recv_tag, force_tag=True)
    logging.debug("Server: Received NumPy request array: %s" % str(arr))
    # print(arr) 
    action_type = arr[0][1].decode()
    action = arr[1][1].decode()
    url = arr[2][1].decode()
    payload = arr[3][1].decode()
    username = arr[4][1].decode()
    password = arr[5][1].decode()
    host = arr[6][1].decode()
    return action_type, action, url, payload, username, password, host


async def send_rest_request(real_url, action, payload, username, password):
    """
    Send simple rest request
    :param real_url:
    :param action:
    :param payload:
    :param username:
    :param password:
    """
    logging.debug("real_url %s, action %s, payload %s, username %s, password %s" %
                  (real_url, action, payload, username, password))
    if payload and payload != 'None':
        send_payload = json.loads(payload)
    else:
        send_payload = None
    try:
        if action == UFMRestAction.GET.value:
            rest_respond = requests.get(real_url, auth=(username, password),
                                        verify=False)
        elif action == UFMRestAction.PUT.value:
            rest_respond = requests.put(real_url, auth=(username, password),
                                        json=send_payload, verify=False)
        elif action == UFMRestAction.SET.value:
            rest_respond = requests.set(real_url, auth=(username, password),
                                        son=send_payload, verify=False)
        elif action == UFMRestAction.POST.value:
            rest_respond = requests.post(real_url, auth=(username, password),
                                         json=send_payload, verify=False)
        else:
            # unknown - probably error
            logging.error("Server: Unknown action %s received. Escape." % action)
            rest_respond = None
    except Exception as e:
        logging.error("Server: Failed to send REST request %s: %s." %
                      (real_url, e))
        rest_respond = None
    return rest_respond


async def handle_rest_request(end_point, recv_tag, send_tag):
    """
    Handle simple rest request
    :param end_point: - end point
    :param recv_tag: - receive tag
    :param send_tag: - send tag
    """
    resp_array = np.chararray((2), itemsize=N_BYTES)
    action_type, action, url, payload, username, password, host = await receive_rest_request(end_point, recv_tag)
    # Separate flow for file transfer
    if action_type == ActionType.ABORT.value:
        logging.error("Server: Abort received - cancel complicated flow")
        return
    if not host or host == 'None':
        host = DEFAULT_HOST_NAME
    if action_type != ActionType.FILE_TRANSFER.value:  # REST REQUEST- RESPOND
        username_pwd = "%s:%s" % (username, password)
        real_url = "https://%s/%s" % (host, url)
        logging.debug("Server: Received: action %s, url %s, payload %s" %
                      (action, url, payload))
        # use requests
        rest_respond = await send_rest_request(real_url, action, payload,
                                               username, password)
        if rest_respond is None:  # failed to send request at all
            logging.error("Server: exception on REST request")
            resp_array[0] = GENERAL_ERROR_NUM
            resp_array[1] = GENERAL_ERROR_MSG
        else:
            if rest_respond.status_code not in SUCCESS_REST_CODE:
                # error
                resp_string = "%s:%s" % (rest_respond.reason,
                                         str(rest_respond.content))
                logging.error("Server: REST request failed: error code %d: %s" %
                              (int(rest_respond.status_code),
                               resp_string))
            else:
                resp_string = rest_respond.content
            resp_array[0] = rest_respond.status_code
            resp_array[1] = resp_string
        await end_point.send(resp_array, tag=send_tag, force_tag=True)
        # recursion
        if action_type == ActionType.IBDIAGNET.value:
            await handle_rest_request(end_point, recv_tag, send_tag)
    else:  # enter to the flow for file_transfer
        logging.debug("Server: Requested transfer of ibdiagnet files")
        await handle_file_transfer(end_point, recv_tag, send_tag)


async def handle_file_transfer(end_point, recv_tag, send_tag):
    """
    Handle transfer of the file from server to client
    :param end_point: end point
    :param recv_tag: receive tag
    :param send_tag: send tag
    """
    logging.debug("Server: Perform ibdiagnet output file transfer")
    try:
        logging.debug("Server: Allocate memory for path")
        file_path = np.chararray((1), itemsize=200)
        logging.debug("Server: Allocate memory for for data size")
        data_size = np.empty(1, dtype=np.uint64)
        await end_point.recv(file_path, tag=recv_tag, force_tag=True)
        file_path_value = file_path[0].decode()
        logging.debug("Server: Received file path %s" % file_path_value)
        f = open(file_path_value, "rb")
        s = f.read()
        data_size[0] = len(s)
    except Exception as e:
        logging.debug("Server: Error filed to read file %s" % e)
        data_size[0] = 0
    logging.debug("Server: The size of data to be sent is %d" % data_size)
    await end_point.send(data_size, tag=send_tag,
                         force_tag=True)  # Requires some parsing with NumPy or struct, as we previously discussed
    if data_size[0] > 0:
        logging.debug("Server: Send data now")
        await end_point.send(s, tag=send_tag, force_tag=True)


def _get_address_info(address=None):
    # Fixed frame size
    frame_size = 10000

    # Header format: Recv Tag (Q) + Send Tag (Q) + UCXAddress.length (Q)
    header_fmt = "QQQ"

    # Data length
    data_length = frame_size - struct.calcsize(header_fmt)

    # Padding length
    padding_length = None if address is None else (data_length - address.length)

    # Header + UCXAddress string + padding
    fixed_size_address_buffer_fmt = header_fmt + str(data_length) + "s"

    assert struct.calcsize(fixed_size_address_buffer_fmt) == frame_size

    return {
        "frame_size": frame_size,
        "data_length": data_length,
        "padding_length": padding_length,
        "fixed_size_address_buffer_fmt": fixed_size_address_buffer_fmt,
    }


def _pack_address_and_tag(address, recv_tag, send_tag):
    address_info = _get_address_info(address)

    fixed_size_address_packed = struct.pack(
        address_info["fixed_size_address_buffer_fmt"],
        recv_tag,  # Recv Tag
        send_tag,  # Send Tag
        address.length,  # Address buffer length
        (
                bytearray(address) + bytearray(address_info["padding_length"])
        ),  # Address buffer + padding
    )

    assert len(fixed_size_address_packed) == address_info["frame_size"]

    return fixed_size_address_packed


def _unpack_address_and_tag(address_packed):
    address_info = _get_address_info()

    recv_tag, send_tag, address_length, address_padded = struct.unpack(
        address_info["fixed_size_address_buffer_fmt"], address_packed,
    )

    # Swap send and recv tags, as they are used by the remote process in the
    # opposite direction.
    return {
        "address": address_padded[:address_length],
        "recv_tag": send_tag,
        "send_tag": recv_tag,
    }


def main_server(request_arguments):
    """
    Main Server flow
    :param request_arguments:
    """
    # register server record
    register_local_address_in_service_record(request_arguments['interface'])

    # dictionary with connection info in {address: (recv_tag, send_tag)} format
    connection_info = {}

    async def handle_rdma_request():
        # Receive address size
        while True:
            address_info = _get_address_info()

            # Receive fixed-size address+tag buffer on tag 0
            packed_remote_address = bytearray(address_info["frame_size"])
            await ucp.recv(packed_remote_address, tag=0)

            # Unpack the fixed-size address+tag buffer
            unpacked = _unpack_address_and_tag(packed_remote_address)
            remote_address = ucp.get_ucx_address_from_buffer(unpacked["address"])
            connection_info[remote_address] = (unpacked["recv_tag"], unpacked["send_tag"])

            # Create endpoint to remote worker using the received address
            ep = await ucp.create_endpoint_from_worker_address(remote_address)
            # prepare np array to receive request
            await handle_rest_request(ep, unpacked["recv_tag"], unpacked["send_tag"])

    asyncio.get_event_loop().run_until_complete(handle_rdma_request())


def main_client(request_arguments):
    """
    Main Client flow
    :param request_arguments:
    """

    async def run(request_arguments):
        sr_service_name = ctypes.c_char_p(SERVICE_NAME)
        sr_device_name = ctypes.c_char_p(str.encode(request_arguments['interface']))
        sr_context = sr_lib.sr_wrapper_create(sr_service_name, sr_device_name, 1)
        addr_holder = bytearray(ADDRESS_SR_HOLDER_SIZE)
        address_buffer = ctypes.c_char * len(addr_holder)
        address_len = sr_lib.sr_wrapper_query(sr_context,
                                              address_buffer.from_buffer(addr_holder), 56)
        if address_len == 0:
            logging.critical("FATAL. Unable to query sr_wrapper and to get "
                             "Server address from Service record")
            return 1
        else:
            logging.debug("sr_wrapper query done, address_len=%d address=%s." %
                          (address_len, addr_holder))
        # get local address
        address = ucp.get_worker_address()
        recv_tag = ucp.utils.hash64bits(os.urandom(16))
        send_tag = ucp.utils.hash64bits(os.urandom(16))
        packed_address = _pack_address_and_tag(address, recv_tag, send_tag)

        remote_address = ucp.get_ucx_address_from_buffer(addr_holder)
        ep = await ucp.create_endpoint_from_worker_address(remote_address)
        # Send local address to server on tag 0
        await ep.send(packed_address, tag=0, force_tag=True)
        ########################################################################
        # Init the request and send it to server
        ########################################################################
        logging.debug("Client: Initialize chararray to sent request to client")
        charar = np.chararray((7, 2), itemsize=200)
        resp_array = np.chararray((2), itemsize=N_BYTES)  # temporarry TODO: exchange size of respond for request
        initialize_request_array(charar, request_arguments)
        logging.debug("Client: Send NumPy request char array")
        await ep.send(charar, tag=send_tag, force_tag=True)  # send the real message
        # recv response in different way and handle differently
        logging.debug("Client: Receive response for simple request")
        resp = np.empty_like(resp_array)
        await ep.recv(resp, tag=recv_tag, force_tag=True)  # receive the echo
        request_status = resp[0]
        # print(resp[1])
        as_string = resp[1].decode()
        ready_string = as_string.replace("N\\/A", "NA")
        # Check if respond was OK. If not - print error
        if int(request_status) not in SUCCESS_REST_CODE:
            if request_arguments['type'] == ActionType.IBDIAGNET.value:
                # need to send cancelation to server - to exit ibdiagnet loop
                logging.error("Client: REST Request Failed: %s" % as_string)
                await cancel_ibdiagnet_respond(ep, send_tag)
            elif request_arguments['type'] == ActionType.COMPLICATED.value:
                await cancel_complicated_respond(ep)
            else:
                logging.error("Client: REST Request Failed: %s" % as_string)
                print(as_string)
        else:  # Suceed
            try:
                parsed_respond = json.loads(ready_string.strip())
                if request_arguments['type'] == ActionType.IBDIAGNET.value:
                    # need to get from respond the name of ibdiagnet job
                    await handle_ibdiagnet_respond(ep, recv_tag, send_tag, parsed_respond, request_arguments)
                elif request_arguments['type'] == ActionType.COMPLICATED.value:
                    await handle_complicated_respond(parsed_respond)
                else:
                    print(json.dumps(parsed_respond, indent=4, sort_keys=True))
            except Exception as e:
                logging.error("Client: Got respond: %s Error %s " % (ready_string, e))

    asyncio.get_event_loop().run_until_complete(run(request_arguments))


def create_base_parser():
    """
    Create an argument parser
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    return parser


def allocate_request_args(parser):
    """
    Definition of arguments
    :param parser:
    """
    request = parser.add_argument_group('request')
    request.add_argument("-i", "--interface", action="store",
                         required=True, default="mlx5_0",
                         choices=None, help="Connection interface name")
    request.add_argument("-r", "--run_mode", action="store",
                         required=True, default=None,
                         choices=["client", "server"], help="Run mode")
    request.add_argument("-u", "--username", action="store",
                         required=None, default="admin", choices=None,
                         help="UFM REST request user name")
    request.add_argument("-p", "--password", action="store",
                         required=None, default="123456", choices=None,
                         help="UFM REST password")
    request.add_argument("-t", "--type", action="store",
                         required=None, default="simple",
                         choices=["simple", "complicated", "ibdiagnet"],
                         help="Action type to be performed")
    request.add_argument("-a", "--rest_action", action="store",
                         required=None, default="GET", choices=["GET", "PUT", "SET", "POST"],
                         help="REST Action to perform")
    request.add_argument("-w", "--rest_url", action="store",
                         required=None, default=None, choices=None,
                         help="UFM REST URL")
    request.add_argument("-s", "--ufm_server_ip", action="store",
                         required=None, default="localhost", choices=None,
                         help="The name or ip of UFM server to send REST request")
    request.add_argument("-c", "--config_file", action="store",
                         required=None, default=None, choices=None,
                         help="Path to the config file name.")
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


def main():
    # arguments parser
    global rdmaRestConfig
    parser = create_base_parser()
    allocate_request_args(parser)
    arguments = vars(parser.parse_args())
    request_arguments = extractRequestArgs(arguments)
    run_mode = request_arguments['run_mode']
    rdmaRestConfig = configparser.ConfigParser()
    config_file_name = request_arguments['config_file']
    if not config_file_name:
        # default configuration file
        config_file_name = os.path.join(WORKING_DIR_NAME,
                                        DEFAULT_CONFIG_FILE_NAME)
    if os.path.isfile(config_file_name):
        try:
            rdmaRestConfig.read(config_file_name)
        except Exception as e:
            error_message = "Failed to read configuration from file %s" % config_file_name
            sys.exit(error_message)
    else:
        error_message = "Configuration file %s not found" % config_file_name
        sys.exit("error_message")
    log_level = rdmaRestConfig.get("Common", "debug_level",
                                   fallback=logging.DEBUG)
    logging.basicConfig(filename=LOG_FILE_PATH,
                        level=logging._nameToLevel[log_level])
    if run_mode == SERVER_MODE_RUN:  # run as server
        logging.info("Running in Server mode")
        main_server(request_arguments)
    else:  # run as client
        main_client(request_arguments)
        logging.info("Running in Client mode")


if __name__ == '__main__':
    main()
