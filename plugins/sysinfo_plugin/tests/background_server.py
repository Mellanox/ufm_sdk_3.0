#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

## imports
import flask
import flask
from flask import Flask,request
from flask_cors import CORS
from flask_ngrok import run_with_ngrok
import json
import threading
import sys


app = Flask(__name__)
#run_with_ngrok(app)
#CORS(app)

LOG_LOCATION="/tmp/recentPost.log"
## create Flask app

@app.route('/dummy',methods=["POST"])    
def post():
    print("DUMMY")
    if request.json:
        print(request.json)
        write_json_file(LOG_LOCATION,request.json)
    else: print(request)
    return {},200
    
def report_error(status_code:int, message:str) -> tuple((dict,int)):
    return {"error": message}, status_code


def write_json_file(file_name:str,data:dict) -> json:
    with open(file_name, "w") as file:
        json.dump(data, file)

class server_thread_wrapper(threading.Thread):
    """Main server on a thread
    """

    def __init__(self,*args,**keywords):
        print("Starting Sysinfo web server", flush=True)
        threading.Thread.__init__(self,*args,**keywords)
        self.killed=False
    
    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        threading.Thread.start(self)
    
    def __run(self): 
        sys.settrace(self.globaltrace) 
        self.__run_backup() 
        self.run = self.__run_backup 
  
    def globaltrace(self, frame, event, arg): 
        if event == 'call': 
            return self.localtrace 
        else: 
            return None
  
    def localtrace(self, frame, event, arg): 
        if self.killed: 
            if event == 'line': 
                raise SystemExit() 
        return self.localtrace 
  
    def kill(self): 
        self.killed = True

def start_server():
    server = server_thread_wrapper(target=app.run)
    server.start()
    return server

def kill_server(server):
    server.kill()
    server.join()


if __name__ == "__main__":
    ## start the server
    server = start_server()
    ## temp wait
    import time
    time.sleep(4)
    ## show the url to copy to access the server
    print("\n\nCopy this address to the Observable notebook!")
    import subprocess
    #subprocess.run(["curl", "-s", "http://localhost:5000/api/tunnels", "|" ,"jq" "-r", "'.tunnels[0].public_url'"])
    subprocess.run(["curl", "-X","POST", "http://localhost:5000/dummy"])
    ## kill the server
    kill_server(server)