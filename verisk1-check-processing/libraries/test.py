import asyncio
from datetime import datetime
import time


async def test_kk(kk):
    await test(kk)


async def test(kk):
    time.sleep(2)
    print(datetime.now(), kk)


async def run_job(n):
    for i in range(n):
        asyncio.ensure_future(test_kk(i))  # fire and forget async_foo()

    print('waiting for future ...')


async def perform_traces(n):
    future_dds_responses = []
    for i in range(n):
        future_dds_responses.append(test(i))

    dds_responses, pending = await asyncio.wait(future_dds_responses)
    print(dds_responses, pending)


def start():

    loop = asyncio.get_event_loop()
    print('start', datetime.now())
    loop.run_until_complete(run_job(5))
    print('end', datetime.now())

    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()

    # The perform_traces method i do all the post method
    print('start', datetime.now())
    task = loop.create_task(perform_traces(5))
    unique_match, error = loop.run_until_complete(task)
    print(unique_match, error)
    loop.close()
    print('end', datetime.now())
