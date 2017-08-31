##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
##############################################################################

import time

class Sleeper(object):
    """This class exists solely to inflate the stack trace, and to be in a
    file where the stack trace won't be affected by editing of the test file
    that uses it.
    """
    _start = _changing_repr_delay = float('inf')

    def __init__(self, *args):
        (self._sleep1, self._sleep2, self._sleep3,
         self._changing_repr_delay) = args

    def __repr__(self):
        now = time.time()
        if self._start + self._changing_repr_delay < now:
            return '<time:%r>' % now
        return object.__repr__(self)

    def __call__(self):
        self._start = time.time()
        self._sleep(self._sleep1)
        self._sleep(self._sleep2)
        self._sleep(self._sleep3)

    def _sleep(self, interval):
        time.sleep(interval)

# Enable this module to be published with ZPublisher.Publish.publish_module()
def bobo_application(sleeper):
    sleeper()
    return "OK"
