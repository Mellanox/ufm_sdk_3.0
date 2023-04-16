#
# Copyright (C) 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import re
import aiohttp
import asyncio
import json


# copied from cabelvalidation from common/switch_json_api
# uses aiohttp instead of requests session

# copied from cablesagent and refactored so as to make more general
# once complete, it will be placed in a 'common' directory, which is something
# that needs to happen soon, as the lines between server and agent are blurred
# due to the requirement that the system funcion when the management network is
# unstable

ASYNC_CMD_TEMPLATE = """\
{
    "execution_type":"async",
    "commands" : $CMD
}
"""

def _exc_handler(loop,context):
    """
    remove unclosed connection warning
    """
    if context["message"] == "Unclosed connection":
        return
    loop.default_exception_handler(context)

class LoginStatus:
    def __init__(self)->None:
        self.json_supported = False
        self.login_success = False

    def __str__(self)->str:
        if not self.json_supported:
            return "Not supported"
        if not self.login_success:
            return "Login Failed"
        return str(True)

    def __repr__(self)->str:
        return str(self)

    def __bool__(self)->bool:
        return self.login_success

class DidntLogin(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class SwitchJSONAPI:
    HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
    HEADERS_JSON = {"Content-Type": "application/json"}
    MAX_JOBS = 10

    def __init__(self) -> None:
        self.verbose = False
        # the following are set during login()
        self.amount_jobs = 0
        self.max_jobs = SwitchJSONAPI.MAX_JOBS
        self.cookie_jar = None
        self.session_aio = None
        self.switch = None
        self.user = None
        self.passwd = None
        self.json_url = None
        self.login_url = None
        self.logout_url = None
        self.json_result = None

    @classmethod
    async def check_alive(cls, switch:str, user:str, passwd:str) -> LoginStatus:
        """
        check if the switch is alive, try to login with user, passwd
        """
        api = cls()
        try:
            login_status = await api.login_aio(switch, user, passwd)
            if login_status.login_success:
                _logout_status = await api.logout_aio()
        except Exception: # pylint: disable=broad-except
            if api.verbose:
                print(f"Failed to login to {switch} as user {user}")
            return LoginStatus()
        return login_status

    @classmethod
    async def check_json_result(cls, result_json:dict) ->bool:
        """
            example returned data
            {
                "results":[
                    {
                        "status":"OK",
                        "executed_command":"docker no start cables_validation",
                        "status_message":"Stopping docker container. Please wait (this can take a minute)...",
                        "data":""
                    },
                    {
                        "status":"OK",
                        "executed_command":"docker remove image cables_validation latest",
                        "status_message":"",
                        "data":""
                    },
                    {
                        "status":"OK",
                        "executed_command":"image delete cables_validation_1.0.0.tar.gz",
                        "status_message":"",
                        "data":""
                    }
                ]
            }
        """

        pass_test = True
        try:
            results = result_json.get("results", None)
            if results is None:
                status = result_json.get("status", None)
                if status == 'ERROR':
                    pass_test = False
            else:
                for entry in results:
                    if entry["status"] != "OK":
                        print(f"executed_command: \"{entry['executed_command']}\"")
                        print(f"status: \"{entry['status']}\"")
                        print(f"status_message: \"{entry['status_message']}\"")
                        pass_test = False
                        break
        except (TypeError,ValueError) as exep:
            print(exep)
            pass_test = False
        return pass_test

    async def logout_aio(self) -> bool:
        """
        logout from the switch return if successful,
        if already logout returns true as well.
        """
        try:
            if asyncio.get_running_loop() is not None:
                asyncio.get_running_loop().set_exception_handler(_exc_handler)
        except Exception as ex:
            print(ex)
        if self.verbose:
            print("---------------------------------------------------------------- logout ---------------------")
        if self.session_aio is None:
            print("Already logout from switch:"+self.switch)
            return True
        try:
            _resp = await self.session_aio.post(self.logout_url, headers=self.HEADERS)
            self.session_aio.cookie_jar.clear()
            await self.session_aio.close()
            return True
        except Exception as exep:
            await self.session_aio.close()
            print("Error logging out: ", exep)
            return False

    def _set_urls(self) -> None:
        """
        set few usuful urls for this switch
        """
        self.login_url = f"https://{self.switch}/admin/launch?script=rh&template=json-request&action=json-login"
        self.logout_url = f"https://{self.switch}/admin/launch?script=rh&template=json-request&action=json-logout"
        self.json_url = f"https://{self.switch}/admin/launch?script=json"

    async def login_aio(self, switch:str, user:str, passwd:str) -> LoginStatus:
        """
        try to login to the switch with the username password
        switch is the ip
        """
        if self.verbose:
            print("-------------------------------------------- login ----------------------")
        self.switch = switch
        self.user = user
        self.passwd = passwd
        self.cookie_jar = aiohttp.CookieJar(unsafe=True)
        self.session_aio = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False),\
                            cookie_jar=self.cookie_jar)
        self._set_urls()
        return await self._do_login_aio()

    async def _do_login_aio(self) -> LoginStatus:
        """
        Do the login and check the cookie from the switch and save it to the session.
        Login thought /admin/launch?script=rh&template=json-request&action=json-login
        """
        try:
            data = {"username": self.user, "password": self.passwd}
            resp = await self.session_aio.post(self.login_url, json=data, headers=self.HEADERS)
            login_status = LoginStatus()
            content_type = resp.headers['content-type']
            status_code = resp.status
            if (status_code == 200 and "json" in content_type) or \
                (status_code == 302 and "text/html" in content_type):
                login_status.json_supported = True
                session_cookie_test = self.session_aio.cookie_jar.filter_cookies("https://"+self.switch)
                if "session" not in session_cookie_test:
                    self.session_aio.cookie_jar.clear()
                else:
                    login_status.login_success = True
                if self.verbose:
                    print(f"Logged in to {self.switch}")
        except ConnectionError as exep:
            #print(exep)
            await self.session_aio.close()
        return login_status

    async def set_port_state(self, port:str, state:str) -> str:
        """
        set the port to a state using the command interface ib 1/{port} shutdown
        """
        #print(f"Setting {port} to {state}")
        if state == "0":

            # "web auto-logout 1",
            cmd = """
                { "commands" : [
                                "interface ib 1/{port} shutdown" ]
                }
        """

        else:
            cmd = """
                { "commands" : [
                                "interface ib 1/{port}",
                                "no shutdown" ]
                }
        """

        cmd = cmd.replace("{port}", port)

        #print("Executing: ", cmd)
        _ret = await self.execute_aio(cmd)
        #print(ret)

    async def get_system_type(self) -> str:
        """
        Get the system type command from the switch
        """
        post_data = "{ \"cmd\" : \"show system type\" }"
        as_json = await self._json_request_aio(post_data)
        value = as_json["data"]["value"]
        return value[0]

    @classmethod
    def extract_port_num(cls, port_name) -> str:
        """
        extract the port number from the switch, 
        """
        port_num = None
        match = re.match(r"IB(\d+)/(\d+)", port_name)
        if match:
            port_num = match.group(2)
        else:
            # support Quantum2: IB1/1/1 IB1/1/2 ... IB1/32/1 IB1/32/2
            # numbering is 'one' indexed 1/1==1 1/2==2, 2/1==3 etc.
            match = re.match(r"IB(\d+)/(\d+)/(\d+)", port_name)
            if match:
                port = int(match.group(2))
                cage = int(match.group(3))
                port_num = f"{(port-1)*2 + cage}"
        return port_num

    async def get_port_status(self) -> list:
        """
        get the ports status using show interface ib status command
        """
        ret = []
        post_data = "{ \"cmd\" : \"show interface ib status\" }"
        as_json = await self._json_request_aio(post_data)
        ports = as_json["data"]
        for port_name, port_data in ports.items():
            port_status = port_data[0]
            lps = port_status["Logical port state"]
            ps = port_status["Physical port state"]
            port_num = self.extract_port_num(port_name)
            if port_num is None:
                continue
            ret.append( {"port" : port_name, "port_num": port_num, "logical" : lps, "physical" : ps }  )

        return ret

    async def execute_aio(self,cmd) -> str:
        """
        execute the command just as is, does not check if it in correct format.
        """
        return await self._json_request_aio(cmd)

    def _get_request_body(self, commands:list, execution_type="sync") -> str:
        return json.dumps({"execution_type": execution_type,
                           "commands": commands})

    async def execute_command_aio(self,cmd:list) -> str:
        """
        execute commands like show version, show power as so on.
        create a request body for them
        """
        return await self._json_request_aio(self._get_request_body(cmd))

    async def _json_request_aio(self,cmd) -> str:
        if self.session_aio is None:
            raise DidntLogin("Cant send command without login first to the switch")
        async with self.session_aio.post(self.json_url,data=cmd,headers=self.HEADERS_JSON) as resp:
            as_json = await resp.json(content_type=None)
            resp.close()
        assert isinstance(as_json,dict)
        return as_json
    
    async def execute_async_commands(self,cmd:list) -> str:
        """
        runs async command which needs time till get the result, for example docker pull
        """
        job_id = await self.execute_async(self._get_request_body(cmd,"async"))
        if job_id is None:
            return job_id
        results = await self.get_job_result(job_id)
        return results

    async def execute_async(self, cmd:list) -> str:
        """
        cmd should contain: "execution_type":"async"
        sample async response
        {
            "job_id": "3345974117",
            "executed_command": "",
            "status": "OK",
            "status_message": "",
            "data": ""
        }
        :return: job_id
        """
        try:
            as_json = await self._json_request_aio(cmd)
            status = as_json["status"]
            if status != "OK":
                print(f"Command failed: {status} -> {as_json['status_message']}")
                return None
            job_id = as_json["job_id"]
            return job_id
        except TypeError as type_error:
            print("Got typeError:"+str(type_error))
            raise type_error

    async def _send_get_jobs_aio(self,job_id:str) -> str:
        """
        get the job data from job id that was already get.
        used in async command like docker pull and docker image...
        """
        job_url = f"{self.json_url}&job_id={job_id}"
        async with self.session_aio.get(job_url, headers=self.HEADERS) as respond:
            as_json = await respond.json(content_type=None)
        return as_json

    async def get_job_result(self, job_id:str) -> str:
        """
        get the results from given job id.
        """
        if not self.session_aio:
            return
        as_json = await self._send_get_jobs_aio(job_id)
        if "results" in as_json:
            return as_json
        status = as_json.get('status')
        if status == 'ERROR':
            if 'Authentication failure' in as_json.get('status_message', ''):
                # re-login
                if self.verbose:
                    print(f"re-login to {self.switch}")
                if not await self._do_login_aio():
                    return as_json
                as_json = await self._send_get_jobs_aio(job_id)
                if "results" in as_json or as_json.get('status') == 'ERROR':
                    return as_json
            else:
                return as_json
        return None