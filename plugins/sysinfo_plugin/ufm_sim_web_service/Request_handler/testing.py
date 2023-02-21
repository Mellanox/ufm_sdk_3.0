import asyncio
import aiohttp
import requests
import json
import time
import math

batch_amount=[1,10,50,100,250,500,1000,2500,5000,7500,10000,20000]

async def call_server():
    session=requests.Session()
    session.verify=False
    session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
    as_json=json.dumps({"callback":"http://localhost:8999/dummy",
                        "commands":["show version"],
                        "switches":["10.209.44.74"], 
                        "username":"admin", "password":"admin", "one_by_one": True})
    respond = session.post("http://127.0.0.1:8999/query",data=as_json)
    if respond.status_code!=200:
        print(respond.status_code)
        await asyncio.sleep(50)

def get_coroutines(amount):
    return [call_server() for i in range(amount)]


async def run(amount):
    """
    Run the coroutines without batching.
    """
    coroutines = get_coroutines(amount)
    await asyncio.gather(*coroutines)


async def run_batched(amount):
    """
    Batch up the coroutines, so the event loop isn't overwhelmed.
    """
    coroutines = get_coroutines(amount)
    iterations = 5
    chunk_size = int(amount / iterations)
    if chunk_size==0:
        chunk_size=1

    remainder = len(coroutines) - (chunk_size * iterations)
    if remainder > 0:
        iterations += math.ceil(remainder / chunk_size)

    for i in range(iterations):
        chunk = coroutines[i * chunk_size : (i + 1) * chunk_size]
        await asyncio.gather(*chunk)


if __name__ == "__main__":
    for i in batch_amount:
        for test in (run, run_batched):
            start = time.time()
            asyncio.run(test(i))
            end = time.time()
            delta = end - start
            print("batch amount of:"+str(i)+" has taken:"+str(delta))