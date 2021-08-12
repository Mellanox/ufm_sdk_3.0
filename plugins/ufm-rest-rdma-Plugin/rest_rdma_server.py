import asyncio
import time
import ucp
import numpy as np
import subprocess
import shlex
from enum import Enum

n_bytes = 2**30
host = ucp.get_address(ifname='ib0')  # ethernet device name
port = 13337


class actionType(Enum):
    SIMPLE = "simple"
    COMPLICATTED = "complicated"
    IBDIAGNET = "ibdiagnet"
    FILE_TRANSFER = "file_transfer"


async def send(ep):
    # recv buffer
#    arr = np.empty(n_bytes, dtype='u1')
    arr = np.chararray((6,2), itemsize=200)
    resp_array= np.chararray((1), itemsize=n_bytes)
    await ep.recv(arr)
   # assert np.count_nonzero(arr) == np.array(0, dtype=np.int64)
    print("Received NumPy array")
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
    # Separate flow for file transfer
    if action_type != actionType.FILE_TRANSFER.value: # REST REQUEST- RESPOND
        username_pwd="%s:%s" % (username, password)
        real_url = "https://r-ufm55.mtr.labs.mlnx/%s" % url
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
        await ep.send(resp_array)
    else: # enter to the flow for file_transfer
        print("Requested transfer of ibdiagnet files")
        await handleFileTransfer(ep)

#    Do not exit on completion - continue
#    await ep.close()
#    lf.close()

async def handleFileTransfer(end_point):
    '''
    Handle transfer of the file from server to client
    :param ep:
    '''

    # recv buffer
#    arr = np.empty(n_bytes, dtype='u1')
    # AT TODO: may be to allocat memory according to path size ....
    #path_size = np.empty(1, dtype=np.uint64)
    #await ep.recv(path_size)
    #file_path = np.chararray((1), itemsize=path_size)
    print("Allocate memory for path")
    file_path = np.chararray((1), itemsize=200)
    print("Allocate memory for for data size")
    data_size = np.empty(1, dtype=np.uint64)
    await end_point.recv(file_path)
    print("Received path")
    file_path_value = file_path[0].decode()
    print("Received file path %s" % file_path_value)
    f = open(file_path_value, "rb")
    s = f.read()
    data_size[0] = len(s)
    print("The size of data to be sent is %d" % data_size)
    await end_point.send(data_size)  # Requires some parsing with NumPy or struct, as we previously discussed
    print("Send data now")
    await end_point.send(s)


async def main():
    global lf
    lf = ucp.create_listener(send, port)
    while not lf.closed():
        await asyncio.sleep(0.1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
