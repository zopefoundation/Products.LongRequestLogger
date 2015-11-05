##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
##############################################################################

import os
import threading
import sys

from collections import OrderedDict
from thread import get_ident
from time import time, sleep
from .dumper import Dumper

TOO_LONG_MSG = "dumping threads took %.2f seconds, longer than interval (%.2f)"

class Monitor(threading.Thread):
    """Logs the stack-trace of a thread until it's stopped
    """

    def __init__(self, log, timeout, interval):
        assert interval > 0, interval
        threading.Thread.__init__(self)
        self.log = log
        self.timeout = max(timeout, interval)
        self.interval = interval
        self.dumpers = OrderedDict()
        self.daemon = True
        self.stopped = False
        self.start()

    def stop(self):
        self.stopped = True
        self.join()

    def run(self):
        dumpers = self.dumpers
        while not self.stopped:
            start_time = time()

            for thread_id, dumper in list(dumpers.items()):
                if dumper is not None and time() - dumper.start > self.timeout:
                    msg = dumper.format_thread()
                    # format_thread could take some time and that dumper
                    # could be gone by now (i.e. the request finished)...
                    if dumpers.get(thread_id) is dumper:
                        self.log.warning(msg)

            elapsed = start_time - time()
            sleep_time = (self.interval if dumpers else self.timeout) - elapsed
            if sleep_time > 0:
                sleep(sleep_time)
            else:
                self.log.error(TOO_LONG_MSG, elapsed, self.interval)

    def __enter__(self):
        thread_id = get_ident()
        self.dumpers[thread_id] = Dumper(thread_id)

    def __exit__(self, t, v, tb):
        thread_id = get_ident()
        del self.dumpers[thread_id]
