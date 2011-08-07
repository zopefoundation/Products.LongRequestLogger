Introduction
============

This product dumps stack traces of long running requests of a Zope2 instance to
a log file. If a request takes more than a configured timeout, it's stack trace
will be dumped periodically to a log file.

It was authored by Leonardo Rochael Almeida, and made possible with developer
time generously donated by `Nexedi <http://www.nexedi.com/>`_, and with design
input from Sébastien Robin and Julien Muchembled.

Installation
============

Buildout Installation
---------------------

Add "Products.LongRequestLogger[standalone]" to the list of eggs of the part
that defines your Zope instance.

Buildout Installation for Old Zope Versions
-------------------------------------------

Add "Products.LongRequestLogger[python24]" to the list of eggs of the part
that defines your Zope instance. This will automatically pull in the
'threadframe' module which is needed for Python versions < 2.5.

Manual Installation for Old Zope Versions
-----------------------------------------

Add the LongRequestLogger package inside your Products instance directory and
install the 'threadframe' module into the Python interpreter used to run Zope.

Configuration
=============

Add (or change) the "environment" section of your zope.conf to something like
this::

    # Products.LongRequestLogger config
    <environment>
          longrequestlogger_file $INSTANCE/log/longrequest.log
          longrequestlogger_timeout 4
          longrequestlogger_interval 2
    </environment>

The following variables are recognised:

 * "longrequestlogger_file": This is a mandatory variable. Its absence means the
   LongRequestLogger monkey-patch to the publication machinery will not be
   applied. It should point to a file where you want the long requests to be
   logged.

 * "longrequestlogger_timeout": The amount of seconds after which long requests
   start being logged. Accepts floating point values and defaults to 2.

 * "longrequestlogger_interval": The frequency at which long requests will have
   their stack trace logged once they have exceeded their 'timeout' above.
   Defaults to 1 and accepts floating point values.

For the curious, the use of environment variables instead of ZConfig directives
is due to two reasons:

 1. The environment variable can be changed at runtime to affect the behaviour
    of the logger.

 2. Old Zope versions don't have the ability to use "product-config" syntax,
    and writing a ZConfig component for just 3 keys is overkill.

Runtime Configuration
---------------------

On the first point above, changing the longrequestlogger_file variable changes
the logging destination for all subsequent requests after the change (and
likely any ongoing request as well), but if Zope is started without that
variable defined, then setting at runtime will not have any effect.

The other two variables can also be dynamically changed as well, and will take
effect at the following request after the change, for all threads in the same
process.

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

