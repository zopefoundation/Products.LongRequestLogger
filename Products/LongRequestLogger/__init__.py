##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
##############################################################################


def initialize(context):
    from . import dumper, monitor
    log = dumper.getLogger()
    if log:
        do_patch(monitor.Monitor(log, **dumper.get_configuration()))

def do_patch(monitor):
    from ZPublisher import Publish
    import logging
    def publish_module_standard(*args, **kw):
        with monitor:
            return publish_module_standard.original(*args, **kw)
    publish_module_standard.original = Publish.publish_module_standard
    logging.getLogger(__name__).info('patching %s.%s',
                                     Publish.__name__,
                                     publish_module_standard.__name__)
    Publish.publish_module_standard = publish_module_standard

def do_unpatch():
    from ZPublisher import Publish
    publish_module_standard = Publish.publish_module_standard
    Publish.publish_module_standard = publish_module_standard.original
