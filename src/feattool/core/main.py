from zope.interface import implements

from feat.common import log

from feattool.gui import main, imports as imports_gui

from feattool.core import imports, settings
from feattool.interfaces import *


class Main(log.FluLogKeeper, log.Logger):
    implements(IMainModel)

    def __init__(self):
        log.FluLogKeeper.__init__(self)
        log.Logger.__init__(self, self)

        self.importer = imports.Imports(self, settings.manager)
        self.importer.load_from_settings()
        self.importer.perform_imports()

        #Setup GUI
        self.controller = main.Controller(self)

        self.import_controller = imports_gui.Controller(self, self.importer)

    ### IMainModel ###

    def show_imports_manager(self):
        self.import_controller.show()

    def finished(self):
        self.controller.show()
