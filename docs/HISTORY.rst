Changelog
=========

2.1.0 (2017-09-11)
------------------

- Log exceptions that are raised while dumping the request. Unprintable
  requests caused the monitor thread to die, resulting in EPIPE errors
  in the ZPublisher wrapper.

- Do never repeat request information, traceback or SQL query if unchanged.

2.0.0 (2015-11-04)
------------------

- Configuration is now done with a "product-config" section in zope.conf,
  instead of environment variables.

- Log queries executed by ZMySQLDA.

- Consolidate stack trace output to a single line if it's the same as the
  previous stack trace.

- Remove the seemly unused mechanism for changing the behaviour at runtime by
  changing environment variables, like redirecting logging to a different
  filename, stopping the logging or changing the timeouts. Log rotation still
  works normally.

- Stop creating and ending one extra thread per request. Instead, a single
  monitoring thread is launched at startup.

- Drop compatibility with Python < 2.6.

1.1.0 (2012-09-10)
------------------

- Some refactoring for code readability.

- Use a `os.pipe()` pair and `select.select()` instead of
  `threading.Condition` to signal when the monitor should stop tracing
  the original thread. This avoids a performance bottleneck in some
  VMWare installations, which seem not to have good performance for locks
  in certain conditions.

- Integrate the logging mechanism with Zope's signal handling and ZConfig's
  rotating file handler so that USR2 signals will cause the long request log
  to get reopened analogous to the access and event log.

1.0.0 (2010-10-28)
------------------

- Initial release
