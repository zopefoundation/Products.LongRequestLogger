.. caution:: 

    This repository has been archived. If you want to work on it please open a ticket in https://github.com/zopefoundation/meta/issues requesting its unarchival.

Introduction
============

This product dumps stack traces of long running requests of a Zope2 instance to
a log file. If a request takes more than a configured timeout, it's stack trace
will be dumped periodically to a log file.

It was authored by Leonardo Rochael Almeida, and made possible with developer
time generously donated by `Nexedi <http://www.nexedi.com/>`_, and with design
input from Sébastien Robin and Julien Muchembled.

.. WARNING:: Products.LongRequestLogger does not work if
   `sauna.reload <https://pypi.python.org/pypi/sauna.reload>`_ is enabled.

Installation
============

Buildout Installation
---------------------

Add "Products.LongRequestLogger" to the list of eggs of the part
that defines your Zope instance.

Configuration
=============

Add (or change) a "<product-config LongRequestLogger>" section of your
zope.conf to something like this::

    <product-config LongRequestLogger>
        logfile $INSTANCE/log/longrequest.log0.log
        timeout 4
        interval 2
    </product-config>

The following variables are recognised:

 * "logfile": This is a mandatory variable. Its absence means the
   LongRequestLogger monkey-patch to the publication machinery will not be
   applied. It should point to a file where you want the long requests to be
   logged.

 * "timeout": The amount of seconds after which long requests
   start being logged. Accepts floating point values and defaults to 2.

 * "interval": The frequency at which long requests will have
   their stack trace logged once they have exceeded their 'timeout' above.
   Defaults to 1 and accepts floating point values.

Interpreting results
====================

It's important to keep in mind a few important facts about the behaviour of
Zope2 applications and threads while looking at the results:

 1. Each thread only handles one request at a time.
 
 2. Slow requests will usually have tracebacks with a common top part and a
    variable bottom part. The key to the cause of the slowdown in a request
    will be in the limit of both.

If you're in a pinch and don't want to parse the file to rank the slowest
URLs for investigation, pick up a time in seconds that's a multiple of your
interval plus the timeout and grep for it. For the default settings, of
time-out and interval, you will find log entries for 4 then 6 then 8 seconds,
so you can do a grep like::

 $ grep -n "Running for 8" longrequest.log 

And decide with URLs show up more. Then you can open the log file, go to the
line number reported and navigate the tracebacks by searching up and down
the file for the same thread id (the number after "Thread" in the reported
lines). Then analise the difference between the tracebacks of a single request
to get a hint on what this particular request is doing and why it is slowing
down.

By doing this for a number of similar requests you will be able to come up with
optimisations or a caching strategy.

