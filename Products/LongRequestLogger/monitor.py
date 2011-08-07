##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
##############################################################################

from threading import Thread
from threading import Condition
from Products.LongRequestLogger import dumper

class Monitor(Thread):
    """Logs the stack-trace of a thread until it's stopped

    m = Monitor(thread.get_ident(), timeout=5, interval=2)

    Wait 5 seconds before dumping the stack-trace of the identified thread
    every 2 seconds.

    m.stop()
    
    Stop the monitoring, whether timed-out or not
    """

    running = False

    def __init__(self,
                 thread_id=None,
                 timeout=None,
                 interval=None):
        Thread.__init__(self)
        self.dumper = dumper.Dumper(thread_id=thread_id)
        self.timeout = timeout or self.dumper.timeout
        self.interval = interval or self.dumper.interval
        self.running_condition = Condition()
        if self.dumper.is_enabled():
            self.running = True
            self.start()

    def stop(self):
        """Stop monitoring the other thread"""
        # this function is called by the other thread, when it wants to stop
        # being monitored
        self.running_condition.acquire()
        try:
            if not self.running:
                return # yes, the finally clause will be run, don't worry
            self.running = False
            self.running_condition.notify()
        finally:
            self.running_condition.release()
        self.join()

    def run(self):
        self.running_condition.acquire()
        self.running_condition.wait(self.timeout)
        # If the other thread is still running by now, it's time to monitor it
        try:
            while self.running:
                self.dumper()
                self.running_condition.wait(self.interval)
        finally:
            self.running_condition.release()
