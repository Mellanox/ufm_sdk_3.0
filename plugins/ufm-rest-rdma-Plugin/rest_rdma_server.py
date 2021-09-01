import asyncio
import time
import ucp
import ctypes 
import sys
import subprocess
import shlex
from enum import Enum
import numpy as np
from ucp._libs import ucx_api
from ucp._libs.utils_test import (
    blocking_flush,
    get_endpoint_error_handling_default,
)
from ucp._libs.arr import Array
import inspect
from pprint import pprint

n_bytes = 2**30

'''
Server:

1. create worker
2. read local address
3. register service record with local address
4. start listening (worker) (progress)
5. on incoming message - should receive addres of remote side
6. call create_from_worker_address with worker from 1 and with remote address (received)
'''
SERVICE_NAME = b"test_service"

# load the lib
sr_test = ctypes.CDLL('/.autodirect/mtrswgwork/atabachnik/workspace/github/Collectx_master_libsr/src/service_record/libservice_record_wrapper.so')

sr_context = ctypes.c_void_p

#sr_wrapper_ctx_t* sr_wrapper_create(const char* service_name, const char* dev_name, int port);
# Function returns
sr_test.sr_wrapper_create.restype = ctypes.c_void_p
# Function gets arguments
sr_test.sr_wrapper_create.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]

#bool sr_wrapper_destroy(sr_wrapper_ctx_t* ctx);
# Function returns
sr_test.sr_wrapper_destroy.restype = ctypes.c_bool
# Function gets arguments
sr_test.sr_wrapper_destroy.argtypes = [ctypes.c_void_p]

#bool sr_wrapper_register(sr_wrapper_ctx_t* ctx, const void* addr, size_t addr_size);
# Function returns
sr_test.sr_wrapper_register.restype = ctypes.c_bool
# Function gets arguments
sr_test.sr_wrapper_register.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]

#bool sr_wrapper_unregister(sr_wrapper_ctx_t* ctx);
# Function returns
sr_test.sr_wrapper_unregister.restype = ctypes.c_bool
# Function gets arguments
sr_test.sr_wrapper_unregister.argtypes = [ctypes.c_void_p]

#size_t sr_wrapper_query(sr_wrapper_ctx_t* ctx, void* addr, size_t addr_size);
# Function returns
sr_test.sr_wrapper_query.restype = ctypes.c_size_t
# Function gets arguments
sr_test.sr_wrapper_query.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]

#--------------------------------------------------------------------
class actionType(Enum):
    SIMPLE = "simple"
    COMPLICATTED = "complicated"
    IBDIAGNET = "ibdiagnet"
    FILE_TRANSFER = "file_transfer"

async def ReceiveRestRequest(end_point):
    '''
    Handle simple rest request
    :param ep: - end point
    '''
    arr = np.chararray((6,2), itemsize=200)
    await ucp.recv(arr, tag=0)
    print("Received NumPy request array:")
    print(arr) 
    action_type = arr[0][1].decode()
    print(action_type)
    action = arr[1][1].decode()
    print(action)
    url = arr[2][1].decode()
    print(url)
    payload = arr[3][1].decode()
    print(payload)
    username = arr[4][1].decode()
    print(username)
    password = arr[5][1].decode()
    print(password)
    return action_type, action, url, payload, username, password

async def handleRestRequest(end_point):
    '''
    Handle simple rest request
    :param ep: - end point
    '''
    resp_array= np.chararray((1), itemsize=n_bytes)
    action_type, action, url, payload, username, password = await ReceiveRestRequest(end_point)
    # Separate flow for file transfer
    if action_type != actionType.FILE_TRANSFER.value: # REST REQUEST- RESPOND
        username_pwd="%s:%s" % (username, password)
        real_url = "https://localhost/%s" % url
        print("Received: action %s, url %s, payload %s" % (action, url, payload))
        if payload and payload != 'None':
            curl_cmd='''curl -d '%s' -H "Content-Type: application/json" -k -X %s -u %s %s''' % (payload, action, username_pwd, real_url)
        else:
            curl_cmd='''curl -k -X %s -u %s %s''' % (action, username_pwd, real_url)
        curl_cmd_list = shlex.split(curl_cmd)
        print("curl command: %s" % curl_cmd)
        result = subprocess.run(curl_cmd_list, stdout=subprocess.PIPE)
        resp_array[0]=result.stdout
        #print(resp_array)
        await end_point.send(resp_array, tag=0, force_tag=True)
        # recursion
        if action_type == actionType.IBDIAGNET.value:
            await handleRestRequest(end_point)
    else: # enter to the flow for file_transfer
        print("Requested transfer of ibdiagnet files")
        await handleFileTransfer(end_point)

async def handleFileTransfer(end_point):
    '''
    Handle transfer of the file from server to client
    :param ep:
    '''
    print("Allocate memory for path")
    file_path = np.chararray((1), itemsize=200)
    print("Allocate memory for for data size")
    data_size = np.empty(1, dtype=np.uint64)
    await ucp.recv(file_path, tag=0)
    print("Received path")
    file_path_value = file_path[0].decode()
    print("Received file path %s" % file_path_value)
    f = open(file_path_value, "rb")
    s = f.read()
    data_size[0] = len(s)
    print("The size of data to be sent is %d" % data_size)
    await end_point.send(data_size, tag=0, force_tag=True)  # Requires some parsing with NumPy or struct, as we previously discussed
    print("Send data now")
    await end_point.send(s, tag=0, force_tag=True)

def registerLocalAddressInServiceRecord():
    address = ucp.get_worker_address()
    serialized_address = bytearray(address)
    print(serialized_address)
    addres_value_len = len(serialized_address)
    print("addres_value_len %d" % addres_value_len)
    address_value_to_send = (ctypes.c_char * addres_value_len).from_buffer(serialized_address)
    # publish local address to server record
    sr_service_name = ctypes.c_char_p(SERVICE_NAME)
    sr_device_name = ctypes.c_char_p(b"mlx5_0")
    sr_context = sr_test.sr_wrapper_create(sr_service_name, sr_device_name, 1)
    if not sr_context:
        print("Unable to allocate sr_wrapper_ctx_t");
        return 1;
    else:
        print("sr_wrapper_ctx_t init done");
    if not sr_test.sr_wrapper_register(sr_context, address_value_to_send, addres_value_len):
        print("Unable to register sr_wrapper")
        return 1

def main():
    # register server record
    registerLocalAddressInServiceRecord()
    async def handleRdmaRequest():
        # Receive address size
        while True:
            address_size = np.empty(1, dtype=np.int64)
            await ucp.recv(address_size, tag=0)
            # Receive address buffer on tag 0 and create UCXAddress from it
            remote_address = bytearray(address_size[0])
            await ucp.recv(remote_address, tag=0)
            remote_address = ucp.get_ucx_address_from_buffer(remote_address)
            # Create endpoint to remote worker using the received address
            ep = await ucp.create_endpoint_from_worker_address(remote_address)
            # prepare np array to receive request
            await handleRestRequest(ep)
    asyncio.get_event_loop().run_until_complete(handleRdmaRequest())

if __name__ == '__main__':
    main()
