##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
##############################################################################

import sys
import unittest
from cStringIO import StringIO
from doctest import OutputChecker
from doctest import REPORT_UDIFF, NORMALIZE_WHITESPACE, ELLIPSIS
import os

class SimpleOutputChecker(OutputChecker):
    # for certain inputs the doctest output checker is much more convenient
    # than manually munging assertions, but we don't want to go through all
    # the trouble of actually writing doctests.

    optionflags = REPORT_UDIFF | NORMALIZE_WHITESPACE | ELLIPSIS

    def __init__(self, want, optionflags=None):
        self.want = want
        if optionflags is not None:
            self.optionflags = optionflags

    def __call__(self, got):
        assert self.check_output(self.want, got, self.optionflags), \
          self.output_difference(self, # pretend we're a doctest.Example
                                 got, self.optionflags)

check_dump = SimpleOutputChecker('''
Thread ...: Started on ...; Running for 0.0 secs; [No request]
Traceback:
...
  File ".../LongRequestLogger/dumper.py", line ..., in format_thread
    traceback.print_stack(frame, file=body)
''')

check_publishing_1_interval_log = SimpleOutputChecker('''
Products.LongRequestLogger WARNING
  Thread ...: Started on ...; Running for 2.0 secs; request: GET http://localhost
retry count: 0
form: {}
other: {'ACTUAL_URL': 'http://localhost',
 'PARENTS': [],
 'PUBLISHED': <Products.LongRequestLogger.tests.common.App object at 0x...>,
 'RESPONSE': HTTPResponse(''),
 'SERVER_URL': 'http://localhost',
 'TraversalRequestNameStack': [],
 'URL': 'http://localhost',
 'interval': 3.5,
 'method': 'GET'}
Traceback:
...
  File ".../LongRequestLogger/__init__.py", line ..., in publish_module_standard
    return publish_module_standard.original(*args, **kw)
  File ".../ZPublisher/Publish.py", line ..., in publish_module_standard
    response = publish(request, module_name, after_list, debug=debug)
...
  File ".../LongRequestLogger/tests/common.py", line ..., in __call__
    Sleeper(interval).sleep()
  File ".../LongRequestLogger/tests/common.py", line ..., in sleep
    self._sleep1()
  File ".../LongRequestLogger/tests/common.py", line ..., in _sleep1
    self._sleep2()
  File ".../LongRequestLogger/tests/common.py", line ..., in _sleep2
    time.sleep(self.interval)
Products.LongRequestLogger WARNING
  Thread ...: Started on ...; Running for 3.0 secs; Same.
''')

check_request_formating = SimpleOutputChecker('''
request: GET http://localhost/foo/bar
retry count: 0
form: {}
other: {'RESPONSE': HTTPResponse(''),
 'SERVER_URL': 'http://localhost',
 'URL': 'http://localhost/foo/bar',
 'method': 'GET'}
''')


config_env_variables = dict(
    longrequestlogger_file=os.devnull,
    longrequestlogger_timeout=None,
    longrequestlogger_interval=None,
)

class TestLongRequestLogger(unittest.TestCase):

    def setUp(self):
        from Products.LongRequestLogger import do_patch, monitor, dumper
        from zope.testing.loggingsupport import InstalledHandler
        self.setTestEnvironment()
        log = dumper.getLogger()
        self.monitor = monitor.Monitor(log, **dumper.get_configuration())
        do_patch(self.monitor)
        self.loghandler = InstalledHandler(log.name)
        self.requests = []

    def tearDown(self):
        from Products.LongRequestLogger import do_unpatch
        do_unpatch()
        self.monitor.stop()
        self.restoreTestEnvironment()
        self.loghandler.uninstall()
        for request in self.requests:
            request.response.stdout.close()
            request.clear()

    def setTestEnvironment(self):
        self.old_env = {}
        for var, value in config_env_variables.items():
            self.old_env[var] = os.environ.pop(var, None)
            if value:
                os.environ[var] = value

    def restoreTestEnvironment(self):
        for var, value in self.old_env.items():
            os.environ.pop(var, None)
            if value is not None:
                os.environ[var] = value

    def makeRequest(self, path='/', **kw):
        # create fake request and response for convenience
        from ZPublisher.HTTPRequest import HTTPRequest
        from ZPublisher.HTTPResponse import HTTPResponse
        stdin = StringIO()
        stdout = StringIO()
        # minimal environment needed
        env = dict(SERVER_NAME='localhost',
                   SERVER_PORT='80',
                   REQUEST_METHOD='GET',
                   SCRIPT_NAME=path)
        response = HTTPResponse(stdout=stdout)
        request = HTTPRequest(stdin, env, response)
        self.requests.append(request)
        return request

    def testDumperFormat(self):
        from Products.LongRequestLogger.dumper import Dumper
        dumper = Dumper()
        check_dump(dumper.format_thread())

    def testDumperRequestExtraction(self):
        # The dumper extract requests by looking for the frame that contains
        # call_object and then looking for the 'request' variable inside it
        from ZPublisher.Publish import call_object
        from Products.LongRequestLogger.dumper import Dumper
        def callable():
            dumper = Dumper()
            frame = sys._current_frames()[dumper.thread_id]
            return dumper.extract_request(frame)

        request = self.makeRequest('/foo')
        retrieved_request = call_object(callable, (), request)
        self.assertTrue(request is retrieved_request)

    def testRequestFormating(self):
        from Products.LongRequestLogger.dumper import Dumper
        dumper = Dumper()
        request = self.makeRequest('/foo/bar')
        check_request_formating(dumper.format_request(request))

    def testPublish(self):
        from ZPublisher.Publish import publish_module_standard
        # Before publishing, there should be no slow query records.
        self.assertFalse(self.loghandler.records)
        # Request taking (timeout + interval + margin) 3.5 seconds...
        request = self.makeRequest('/', interval=3.5)
        request['interval'] = 3.5
        publish_module_standard('Products.LongRequestLogger.tests.common',
                                request=request,
                                response=request.response,
                                debug=True)
        # ...should generate query log records like these
        check_publishing_1_interval_log(str(self.loghandler))

def test_suite():
    return unittest.TestSuite((
         unittest.makeSuite(TestLongRequestLogger),
    ))
