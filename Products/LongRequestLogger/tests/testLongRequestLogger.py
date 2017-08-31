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
    stack = traceback.extract_stack(frame)
''')

_request = '''request: GET http://localhost
retry count: 0
form: {}
other: {'ACTUAL_URL': 'http://localhost',
 'PARENTS': [],
 'PUBLISHED': <function bobo_application at 0x...>,
 'RESPONSE': HTTPResponse(''),
 'SERVER_URL': 'http://localhost',
 'TraversalRequestNameStack': [],
 'URL': 'http://localhost',
 'method': 'GET',
 'sleeper': <%s...>}'''

_traceback = '''Traceback:
...
  File ".../LongRequestLogger/__init__.py", line ..., in publish_module_standard
    return publish_module_standard.original(*args, **kw)
  File ".../ZPublisher/Publish.py", line ..., in publish_module_standard
    response = publish(request, module_name, after_list, debug=debug)
...
  File ".../LongRequestLogger/tests/common.py", line ..., in bobo_application
    sleeper()
  File ".../LongRequestLogger/tests/common.py", line ..., in __call__
    self._sleep(self._sleep%s)
  File ".../LongRequestLogger/tests/common.py", line ..., in _sleep
    time.sleep(interval)'''

check_publishing_1_interval_log = SimpleOutputChecker('''
Products.LongRequestLogger WARNING
  Thread ...: Started on ...; Running for 2.0 secs; %s
%s
Products.LongRequestLogger WARNING
  Thread ...: Started on ...; Running for 3.0 secs; Same.
Products.LongRequestLogger WARNING
  Thread ...: Started on ...; Running for 4.0 secs; %s
Products.LongRequestLogger WARNING
  Thread ...: Started on ...; Running for 5.0 secs; %s
Products.LongRequestLogger WARNING
  Thread ...: Started on ...; Running for 6.0 secs; %s
%s
''' % (_request % '...Sleeper object at 0x', _traceback % 1,
       _traceback % 2,
       _request % 'time:',
       _request % 'time:', _traceback % 3))

check_request_formating = SimpleOutputChecker('''
request: GET http://localhost/foo/bar
retry count: 0
form: {}
other: {'RESPONSE': HTTPResponse(''),
 'SERVER_URL': 'http://localhost',
 'URL': 'http://localhost/foo/bar',
 'method': 'GET'}
''')


class TestLongRequestLogger(unittest.TestCase):

    def setUp(self):
        from Products.LongRequestLogger import do_patch, monitor, dumper
        from zope.testing.loggingsupport import InstalledHandler
        dumper.config = dict(logfile=os.devnull)
        log = dumper.getLogger()
        self.monitor = monitor.Monitor(log, **dumper.get_configuration())
        do_patch(self.monitor)
        self.loghandler = InstalledHandler(log.name)
        self.requests = []

    def tearDown(self):
        from Products.LongRequestLogger import do_unpatch
        do_unpatch()
        self.monitor.stop()
        self.loghandler.uninstall()
        for request in self.requests:
            request.response.stdout.close()
            request.clear()

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
        from .common import Sleeper
        from ZPublisher.Publish import publish_module_standard
        # Before publishing, there should be no slow query records.
        self.assertFalse(self.loghandler.records)
        request = self.makeRequest('/')
        # 1. All information is dumped on initial timeout.
        # 2. 1 second later, a single line is logged
        #    because there's no new information.
        # 3. Only the traceback changes and it is logged
        #    without request information.
        # 4. The request changes with same traceback:
        #    only the request is logged.
        # 5. The request changes with different traceback: full dump.
        request['sleeper'] = Sleeper(3.5, 2, 1, 4.5)
        publish_module_standard(Sleeper.__module__,
                                request=request,
                                response=request.response,
                                debug=True)
        # ...should generate query log records like these
        check_publishing_1_interval_log(str(self.loghandler))

def test_suite():
    return unittest.TestSuite((
         unittest.makeSuite(TestLongRequestLogger),
    ))
