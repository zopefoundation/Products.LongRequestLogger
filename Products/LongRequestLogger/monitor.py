##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
##############################################################################

import os, sys, threading, time
from collections import deque
from select import select
from thread import get_ident
from .dumper import Dumper


class Monitor(threading.Thread):
    """Logs the stack-trace of a thread until it's stopped
    """

    def __init__(self, log, timeout, interval):
        assert interval > 0, interval
        threading.Thread.__init__(self)
        self.log = log
        self.timeout = timeout
        self.interval = interval
        self.lock = threading.Lock()
        self.dumpers = deque()
        self.event_pipe = os.pipe()
        self.daemon = True
        self.start()

    def stop(self):
        with self.lock:
            if not self.event_pipe:
                return
            os.close(self.event_pipe[1])
            self.event_pipe = None
        self.join()

    def run(self):
        r = self.event_pipe[0]
        try:
            l = self.lock
            dumpers = self.dumpers
            t = 0
            while 1:
                t = select([r], (), (), t)[0] and (os.read(r, 8) or sys.exit())
                with l:
                    if dumpers:
                        while 1:
                            t = dumpers[0].next_dump - time.time()
                            if t > 0:
                                break
                            dumper = dumpers.popleft()
                            self.log.warning(dumper.format_thread())
                            dumper.next_dump = time() + self.interval
                            self.push(dumper)
                    else:
                        t = None
        finally:
            os.close(r)

    def push(self, dumper):
        dumpers = self.dumpers
        i = j = len(dumpers)
        while i and dumper.next_dump < dumpers[-1].next_dump:
            dumpers.rotate()
            i -= 1
        dumpers.append(dumper)
        dumpers.rotate(i - j)
        return i

    def __enter__(self):
        with self.lock:
            dumper = Dumper()
            dumper.next_dump = dumper.start + self.timeout
            if not self.push(dumper) and self.event_pipe:
                os.write(self.event_pipe[1], '\0')

    def __exit__(self, t, v, tb):
        with self.lock:
            thread_id = get_ident()
            for i, dumper in enumerate(self.dumpers):
                if dumper.thread_id == thread_id:
                    del self.dumpers[i]
                    if not i and self.event_pipe:
                        os.write(self.event_pipe[1], '\0')
                    break
