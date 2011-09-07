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

from feat.common import log

from feattool import data
from feattool.core import settings


class Controller(log.Logger, log.LogProxy):

    def __init__(self, logger, model):
        log.Logger.__init__(self, logger)
        log.LogProxy.__init__(self, logger)

        self.model = model
        self.builder = gtk.Builder()

    def show(self):
        self.builder.add_from_file(data.path('ui', 'main.ui'))
        self.view = View(self, self.builder, self.model)
        self.view.window.show_all()

    def hide(self):
        self.view.window.hide_all()

    def save_clicked(self, button):
        settings.manager.save()

    def add_clicked(self, button):
        self.model.append()

    def remove(self, path):
        iter = self.model.get_iter(path)
        value = self.model.remove(iter)

    def import_clicked(self, path):
        iter = self.model.get_iter(path)
        self.model.do_import(iter, force=True)


class View(log.Logger):

    def __init__(self, controller, builder, model):
        self.controller = controller
        self.builder = builder
        self.model = model

        self.window = None

        self._setup_window()
        self._setup_list()
        self._setup_buttons()

    def _setup_buttons(self):
        save = self.builder.get_object('save_settings')
        save.connect('clicked', self.controller.save_clicked)

        add = self.builder.get_object('add_import')
        add.connect('clicked', self.controller.add_clicked)

        remove = self.builder.get_object('remove_import')
        remove.connect('clicked', self._remove_clicked)

        import_b = self.builder.get_object('import_button')
        import_b.connect('clicked', self._import_clicked)

    def _remove_clicked(self, button):
        path, _ = self.ilist.get_cursor()
        self.controller.remove(path)

    def _import_clicked(self, button):
        path, _ = self.ilist.get_cursor()
        self.controller.import_clicked(path)

    def _setup_window(self):
        self.window = self.builder.get_object('import_manager')
        self.window.set_title('Import manager')
        self.window.resize(300, 240)
        self.window.connect('destroy', lambda window: self.controller.hide())

    def _setup_list(self):
        self.ilist = ImportList(self.model)
        self.ilist.show_all()
        self.builder.get_object('imports_pane').add(self.ilist)


class ImportList(gtk.TreeView):

    def __init__(self, model=None):
        gtk.TreeView.__init__(self, model)

        self._setup_columns()

    def _setup_columns(self):
        toggle_renderer = gtk.CellRendererToggle()
        toggle_renderer.connect('toggled', self._auto_toggle_toggled)
        col = gtk.TreeViewColumn('Auto')
        col.pack_start(toggle_renderer, False)
        col.add_attribute(toggle_renderer, 'active', 1)
        self.append_column(col)

        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('edited', self._edited)
        col = gtk.TreeViewColumn('Canonical name')
        col.pack_start(renderer, True)
        col.add_attribute(renderer, 'text', 0)
        self.append_column(col)

    def _edited(self, render, path, new_text):
        model = self.get_model()
        iter = model.get_iter(path)
        model.set_value(iter, 0, new_text)

    def _auto_toggle_toggled(self, cell, path):
        model = self.get_model()
        iter = model.get_iter((int(path), ))
        val = model.get_value(iter, 1)

        val = not val
        model.set(iter, 1, val)
