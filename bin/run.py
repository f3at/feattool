#!/usr/bin/python
from twisted.internet import gtk2reactor
gtk2reactor.install()

from twisted.internet import reactor

from feat.common import log

from feattool.core.main import Main

if __name__ == '__main__':
    log.FluLogKeeper.init()
    Main()

    reactor.run()
