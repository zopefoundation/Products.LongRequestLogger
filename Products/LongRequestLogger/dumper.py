##############################################################################
#
# Copyright (c) 2010,2012 Zope Foundation and Contributors.
#
##############################################################################

from cStringIO import StringIO
from pprint import pformat
from thread import get_ident
import Signals.Signals
import ZConfig.components.logger.loghandler
import ZServer.BaseLogger
import logging
import os
import time
import traceback
import sys
from . import __name__ as logger_name

try:
    from signal import SIGUSR2
except ImportError:
    # Windows doesn't have these (but also doesn't care what the exact
    # numbers are)
    SIGUSR2 = 12

formatter = logging.Formatter("%(asctime)s - %(message)s")

DEFAULT_TIMEOUT = 2
DEFAULT_INTERVAL = 1

def getLogger(name=logger_name):
    logfile = os.environ.get('longrequestlogger_file')
    if logfile:
        log = logging.getLogger(name)
        log.propagate = False
        # to imitate FileHandler
        logfile = os.path.abspath(logfile)
        if os.name == 'nt':
            rotate = Signals.Signals.LogfileRotateHandler
            handler = ZConfig.components.logger.loghandler.Win32FileHandler(
                logfile)
        else:
            rotate = Signals.Signals.LogfileReopenHandler
            handler = ZConfig.components.logger.loghandler.FileHandler(
                logfile)
        handler.formatter = formatter
        # Register with Zope 2 signal handlers to support log rotation
        if Signals.Signals.SignalHandler:
            Signals.Signals.SignalHandler.registerHandler(
                SIGUSR2, rotate([handler]))
        log.addHandler(handler)
        return log

def get_configuration():
    return dict(
        timeout=float(os.environ.get('longrequestlogger_timeout', 
                                       DEFAULT_TIMEOUT)),
        interval=float(os.environ.get('longrequestlogger_interval', 
                                       DEFAULT_INTERVAL)),
    )

SUBJECT_FORMAT = "Thread %s: Started on %.1f; Running for %.1f secs; "
REQUEST_FORMAT = """\
request: %(method)s %(url)s
retry count: %(retries)s
form: %(form)s
other: %(other)s
"""

class Dumper(object):

    _last = None

    def __init__(self, thread_id=None):
        if thread_id is None:
            # assume we're being called by the thread that wants to be
            # monitored
            thread_id = get_ident()
        self.thread_id = thread_id
        self.start = time.time()

    def format_request(self, request):
        if request is None:
            return "[No request]\n"
        query = request.get("QUERY_STRING")
        return REQUEST_FORMAT % {
            "method": request["REQUEST_METHOD"],
            "url": request.getURL() + ("?" + query if query else ""),
            "retries": request.retry_count,
            "form": pformat(request.form),
            "other": pformat(request.other),
        }

    def extract_request(self, frame):
        # We try to fetch the request from the 'call_object' function because
        # it's the one that gets called with retried requests.
        # And we import it locally to get even monkey-patched versions of the
        # function.
        from ZPublisher.Publish import call_object
        func_code = call_object.func_code #@UndefinedVariable
        while frame is not None:
            if frame.f_code is func_code:
                return frame.f_locals.get('request')
            frame = frame.f_back

    def format_thread(self):
        subject = SUBJECT_FORMAT % (self.thread_id, self.start,
                                    time.time() - self.start)
        body = StringIO()
        frame = sys._current_frames()[self.thread_id]
        try:
            body.write(self.format_request(self.extract_request(frame)))
            body.write("Traceback:\n")
            traceback.print_stack(frame, file=body)
        finally:
            del frame
        body = body.getvalue()
        if self._last == body:
            return subject + "Same.\n"
        self._last = body
        return subject + body
