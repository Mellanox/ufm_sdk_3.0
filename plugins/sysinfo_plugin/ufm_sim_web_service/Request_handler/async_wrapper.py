"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2001-2021.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Samer Deeb
@date:   Sep 30, 2021
"""

import functools
import logging
import threading

from twisted.internet import reactor, threads
from twisted.internet.task import LoopingCall

_logger = logging.getLogger('ufm')


def _callable_wrap(callable, *args, **kw):
    try:
        res = callable(*args, **kw)
    except:
        _logger.exception("Unexpected exception in asyncio")
        res = None
    return res


def _call_later_in_mainthread(event, delayed_list, delay, callable, *args, **kw):
    # this call_later will be called from main thread and hence will return the delayed call
    delayed_call = call_later(delay, callable, *args, **kw)
    # save the delayed call in the list to be used by caller.
    # as call_from_thread does not return anything
    delayed_list.append(delayed_call)
    # set the event so the caller can get the delayed call
    event.set()

def call_later(delay, callable, *args, **kw):
    if threading.current_thread() is threading.main_thread():
        callable = functools.partial(_callable_wrap, callable, *args, **kw)
        return reactor.callLater(delay, callable)
    # Since twisted is not thread safe and we are not running on the main thread,
    # let's move to main thread by calling call_from_thread 

    # create a list to store the delayed call object, that will be created in the main thread
    delayed_list = list()
    # create an event to notify us once the delayed call object is read
    event = threading.Event()
    # switch to main thread
    call_from_thread(_call_later_in_mainthread, event, delayed_list, delay, callable, *args, **kw)
    # wait until delayed call object is ready
    event.wait()
    # return the delayed call object
    return delayed_list[0] if delayed_list else None


def call_in_thread(callable, *args, **kw):
    callable = functools.partial(_callable_wrap, callable, *args, **kw)
    reactor.callInThread(callable)


def call_from_thread(callable, *args, **kw):
    callable = functools.partial(_callable_wrap, callable, *args, **kw)
    reactor.callFromThread(callable)


if __name__ == "__main__":

    def aSillyBlockingMethod(x):
        import time
        time.sleep(2)
        print(x)
        raise ValueError("test")

    # run method in thread
    call_later(2, aSillyBlockingMethod, "2 seconds have passed")
    reactor.run()
