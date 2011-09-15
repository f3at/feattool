# F3AT - Flumotion Asynchronous Autonomous Agent Toolkit
# Copyright (C) 2010,2011 Flumotion Services, S.A.
# All rights reserved.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# See "LICENSE.GPL" in the source distribution for more information.

# Headers in this file shall remain intact.
from zope.interface import implements

from feat.common import log

from feattool.gui import main, imports as imports_gui

from feattool.core import imports, settings, simulation, journal
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
