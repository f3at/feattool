from zope.interface import implements

from feat.common import log

from feattool.gui import main

from feattool.core import simulation
from feattool.interfaces import *


class Main(log.FluLogKeeper, log.Logger):
    implements(IMainModel)

    def __init__(self):
        log.FluLogKeeper.__init__(self)
        log.Logger.__init__(self, self)

        #Setup GUI
        self.controller = main.Controller(self)

    ### IMainModel ###

    def finished(self):
        self.controller.show()
