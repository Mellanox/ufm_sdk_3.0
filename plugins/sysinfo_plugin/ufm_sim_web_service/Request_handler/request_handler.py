#
# Copyright (C) 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import asyncio
import logging
import time
import aiohttp

try:
    from SwitchAPI import SwitchJSONAPI
except ModuleNotFoundError:
    from .SwitchAPI import SwitchJSONAPI

class RequestHandler:
    """
    Handling the requests from the user, gets the ips and commands to do on them.
    On default have default setting, need to check
    Have several modes:
    * all_at_once - if not None, each ip that finish send the results already to the callback, the callback is all_at_once
    * is_async - if the commands are async, and client dont need to wait for the switch to get the information.
    """
    def __init__(self, switches_ips:list, commands:list, ac:list=None, ip_to_guid:dict=None,
                 all_at_once:str=None, is_async:bool=False, auto_respond:dict=None) -> None:
        
        self.ip_to_guid = ip_to_guid
        if ip_to_guid is None:
            self.ip_to_guid = {}
        self.switches=switches_ips
        self.commands=commands
        self.ac=ac
        self.is_async=is_async
        self.one_by_one_callback=all_at_once
        self.verbose = False

        if not self.ac or len(self.ac) != 2:
            self.ac = ["admin","admin"]

        self.is_executing=False
        self.latest_respond = {}
        self.auto_respond={} if auto_respond is None else auto_respond
        self.latest_respond.update(self.auto_respond)
        self.switches_apis={}

    async def post_commands(self) -> dict:
        """
        post the commands once!
        Login to all the switches, then execute all the commands,
         and finally logout all the switches
        """
        start_time=time.time()
        login_tasks=[]
        logout_tasks=[]
        tasks=[]
        for switch in self.switches:
            switch_api=SwitchJSONAPI()
            login_tasks.append(switch_api.login_aio(switch,self.ac[0],self.ac[1]))
            logout_tasks.append(switch_api.logout_aio())
            if not self.is_async:
                tasks.append(self._send_for_switch_commands_all(switch_api))
            else:
                tasks.append(self._send_async_commands(switch_api))
        await asyncio.gather(*login_tasks)
        login_time=time.time()
        await asyncio.gather(*tasks)
        gather_time=time.time()
        await asyncio.gather(*logout_tasks)
        overall_time=time.time()
        if self.one_by_one_callback is not None and len(self.auto_respond)>0:
            auto_tasks=[]
            for key,value in self.auto_respond.items():
                auto_tasks.append(self.save_results(self.one_by_one_callback,{key:value}))
            await asyncio.gather(*tasks)
        if self.verbose:
            print("login:"+str(login_time-start_time)+",gather:"+str(gather_time-login_time)+
            ",logout:"+str(overall_time-gather_time)+",overall:"+str(overall_time-start_time))
        return self.latest_respond

    async def _execute_commands(self):
        """
        only execute commands, assume the switchAPIs have already login and have cookie
        """
        if self.is_executing:
            pass
        self.is_executing=True
        tasks=[]
        for switchApi in self.switches_apis:
            if not self.is_async:
                tasks.append(self._send_for_switch_commands_all(switchApi))
            else:
                tasks.append(self._send_async_commands(switchApi))
        await asyncio.gather(*tasks)
        self.is_executing=False
        return self.latest_respond

    async def post_commands_once(self):
        """
        create a thread of login execute command and logout foreach of the switches
        """
        tasks=[]
        start_time=time.time()
        for switch in self.switches:
            switch_api=SwitchJSONAPI()
            tasks.append(self._send_once_switch(switch_api,switch))
        await asyncio.gather(*tasks)
        end_time=time.time()
        if self.verbose:
            print("took overall on once per switch:"+str(end_time-start_time))
        return self.latest_respond

    async def _send_once_switch(self,switchAPI:SwitchJSONAPI,switch:str) -> dict:
        """
        run for on one switch the whole login execute and logout
        """
        result = await switchAPI.login_aio(switch,self.ac[0],self.ac[1])
        if not result:
            self.latest_respond[switch]={"error":"Cant login to the switch"}
            return result
        if not self.is_async:
            await self._send_for_switch_commands_all(switchAPI)
        else:
            await self._send_async_commands(switchAPI)
        result = await switchAPI.logout_aio()
        return self.latest_respond


    async def _send_for_switch_commands(self,switchAPI: SwitchJSONAPI) -> None:
        """
        send sync commands one after anther,
        if one by one callback is not none, send the results to the callback
        """
        dict_result={}
        raw_results = []
        for command in self.commands:
            results = await switchAPI.execute_command_aio(command)
            raw_results.append(results)
        key = switchAPI.switch
        key_dict = "switch_" + (self.ip_to_guid[key] if len(self.ip_to_guid) > 0 
                           and key in self.ip_to_guid else key)
        dict_result[key_dict]=self.proccess_results(raw_results)
        if self.one_by_one_callback is not None:
            await self.save_results(self.one_by_one_callback,dict_result)
        else:
            self.latest_respond.update(dict_result)

    async def _send_for_switch_commands_all(self,switchAPI: SwitchJSONAPI) -> dict:
        """
        send sync commands all at once,
        if one by one callback is not none, send the results to the callback
        """
        raw_result = await switchAPI.execute_command_aio(self.commands)
        dict_result ={}
        key = switchAPI.switch
        if len(self.ip_to_guid) > 0 and key in self.ip_to_guid:
            key=self.ip_to_guid[key]
        else:
            key="switch_" + key
        
        dict_result[key]=self.proccess_results(raw_result)
        if self.one_by_one_callback is not None:
            await self.save_results(self.one_by_one_callback,dict_result)
        else:
            self.latest_respond.update(dict_result)
        return self.latest_respond

    async def _send_async_commands(self,switchAPI:SwitchJSONAPI) ->dict:
        """
        send sync commands one after anther, save all to latest respond
        """
        for command in self.commands:
            raw_result = await switchAPI.execute_command_aio([command])
            key = switchAPI.switch
            if key in self.ip_to_guid:
                key = self.ip_to_guid[key]
            else:
                key = "switch_" + key
            if raw_result is None:
                self.latest_respond[key]={"error":"command could not be received"}
            self.latest_respond[key]=self.proccess_results(raw_result)
        return self.latest_respond
    
    def proccess_results(self,raw_data):
        """
        process the results of the raw data to get the answers from each execute command
        """
        respond={}
        if 'results' in raw_data:
            raw_data_results=raw_data['results']
        else:
            respond[raw_data['executed_command']] = raw_data
            return respond
        for answer in raw_data_results:
            respond[answer['executed_command']] = answer
        return respond
    
    def login_to_all(self) -> None:
        asyncio.run(self._login_to_all())

    def logout_to_all(self) -> None:
        asyncio.run(self._logout_to_all())

    def execute_commands(self) -> None:
        asyncio.run(self._execute_commands())

    def execute_commands_and_save(self,callback) -> None:
        self.execute_commands()
        if self.one_by_one_callback is None: 
            asyncio.run(self.save_results(callback=callback,results=self.latest_respond))


    async def _login_to_all(self) -> None:
        """
        try login to all the switches the user gave
        """
        for switch in self.switches:
            switch_api=SwitchJSONAPI()
            login_status = await switch_api.login_aio(switch,self.ac[0],self.ac[1])
            if login_status:
                self.switches_apis[switch] = switch_api
            else:
                self.latest_respond[switch] = "Could not connect to switch"
    
    async def _logout_to_all(self) -> None:
        """
        try to logout from all the switches, if never login return successful
        """
        for switch_api in self.switches_apis:        
            _resp= await switch_api.logout_aio()
            if not _resp:
                logging.error(f"Could not logout from {switch_api.switch}")

    async def save_results(self, callback, results):
        """
        save the results to the callback location
        """
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.post(callback,json=results) as respnd:
                return respnd.status, respnd.reason

async def __run_experimate_sync__():
    """
    this function is for testing the plugin on 500 simulated switches that already up
    """
    for amount_of_switches in [1,5,10,20,50,100,250,500]:
        for amount_of_commands in [1,10,100,1000]:
            ip=[]
            for j in range(max(1,amount_of_switches-256)):
                for i in range(min(amount_of_switches-j*256,(254 if j==0 else 256))):
                    ip.append('172.18.'+str(j)+'.'+str(i+2 if j==0 else i))
            commands=[]
            for i in range(amount_of_commands):
                commands.append("show version")
                ##same command over and over but it make respond the same amount of commands
            rh = RequestHandler(ip,commands)
            #result = await rh.post_commands()
            await rh.post_commands_once()
            print("number of commands:"+str(amount_of_commands)+\
                ',number of switches:'+str(amount_of_switches))
            #print(result)


async def __run_example_sync__():
    start_time=time.time()
    ip = ['10.209.224.32',"10.209.27.19","10.209.36.113","10.209.36.122",]#,"10.209.226.7"
    commands=["show inventory"]#,"show version"," show system type"]
    rh = RequestHandler(ip,commands)
    result = await rh.post_commands()
    print(result)
    print((time.time()-start_time))

async def __run_exmaple_async__():
    start_time = time.time()
    ip = ['10.209.224.32']#"10.209.226.7"]#"10.209.27.19"]
    commands=["docker ?"]#,"show version"," show system type"]
    rh = RequestHandler(ip,commands,is_async=True)
    result = await rh.post_commands()
    end_time = time.time()
    print(result)
    print("time took:"+str(end_time-start_time))

async def __run_testing_():

    batch=[1,5,10]
    ip = ['10.209.27.19']
    command = ['show version']
    rh = RequestHandler(ip,command)
    for i in batch:
        tasks = [rh.post_commands_once() for j in range(i)]
        start_time=time.time()
        await asyncio.gather(*tasks)
        end_time=time.time()
        print("batch:"+str(i)+", took me "+str(end_time-start_time))


if __name__ == "__main__":
    asyncio.run(__run_testing_())
    #asyncio.run(__run_example_sync__())
    #run_example_twisted()
    