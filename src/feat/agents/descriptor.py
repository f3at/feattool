# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import uuid

from . import document


class Descriptor(document.Document):

    def __init__(self, uid=None, shard='lobby'):
        document.Document.__init__(self, uid or str(uuid.uuid1()))
        self.shard = shard
