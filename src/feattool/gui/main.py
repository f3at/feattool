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
import gtk

from twisted.internet import reactor

from feat.common import log

from feattool import data
from feattool.core import component


class Controller(log.Logger, log.LogProxy):
    """
    This is the controller of simulation component.
    """

    def __init__(self, model):
        log.Logger.__init__(self, model)
        log.LogProxy.__init__(self, model)

        self.model = model
        self.builder = gtk.Builder()
        self.builder.add_from_file(data.path('ui', 'main.ui'))

        self.info('Loading main window...')
        self.main = MainWindow(self, self.builder)
        self.show()
        self.info('Done loading main window...')

    def show(self):
        self.main.window.show_all()

    def hide(self):
        self.main.window.hide_all()

    def component_selected(self, name):
        comp = component.query(name)
        if comp is None:
            self.error('Component with name %r not found!', name)
            return
        comp.construct_window(self.model)
        self.hide()

    def quit(self):
        reactor.stop()


class MainWindow(log.Logger):

    def __init__(self, controller, builder):
        log.Logger.__init__(self, controller)

        self.controller = controller
        self.builder = builder
        self.window = None

        self._setup_window()
        self._setup_components()

    def _setup_window(self):
        self.window = self.builder.get_object('main_window')
        self.window.set_title('Feat Tool')
        self.window.resize(500, 300)
        self.window.connect('destroy', self._destroy_event)

    def _setup_components(self):
        components = component.get_all()
        rows = len(components) / 2
        if len(components) % 2 != 0 or rows == 0:
            rows += 1

        table = gtk.Table(rows=rows, columns=2, homogeneous=True)
        obj = self.builder.get_object('main_box')
        obj.add(table)
        obj.show()

        for comp, index in zip(components, range(len(components))):
            widget = comp.get_menu_presentation()
            row = index / 2
            column = index % 2
            widget.connect('clicked', self._component_clicked, comp.name)
            widget.show()
            table.attach(widget,
                         column, column + 1,
                         row, row + 1, )

    def _component_clicked(self, button, component_name):
        self.controller.component_selected(component_name)

    def _destroy_event(self, window):
        self.quit()

    def quit(self):
        self.window.hide()
        self.controller.quit()
