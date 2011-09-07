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

from feat.common import reflect, log


class Imports(gtk.ListStore, log.Logger):

    def __init__(self, logger, settings):
        gtk.ListStore.__init__(self, str, bool)
        log.Logger.__init__(self, logger)
        self.settings = settings

        self.connect('row-changed', self._save_entry)
        self.connect('row-inserted', self._save_entry)

    def load_from_settings(self):
        self.clear()
        if not self.settings.has_section('imports'):
            self.settings.add_section('imports')
        for key, value in self.settings.items('imports'):
            row = self.append()
            self.set(row, 0, key)
            self.set(row, 1, value == 'True')

    def perform_imports(self):

        def do_import(model, path, iter):
            self.do_import(iter)

        self.foreach(do_import)

    def do_import(self, iter, force=False):
        canonical_name, auto = self._parse_row(iter)

        if force or auto:
            try:
                reflect.named_module(canonical_name)
            except ImportError as e:
                self.error('Error importing: %r', e)

    def remove(self, iter):
        canonical_name, auto = self._parse_row(iter)
        gtk.ListStore.remove(self, iter)
        self.settings.remove_option('imports', canonical_name)

    def _parse_row(self, iter):
        canonical_name = self.get_value(iter, 0)
        auto = self.get_value(iter, 1)
        return canonical_name, auto

    def _save_entry(self, model, path, iter):
        canonical_name, auto = self._parse_row(iter)
        if canonical_name is not None:
            self.settings.set('imports', canonical_name, auto)
        self._remove_stale()

    def _remove_stale(self):
        existing = [self.get_value(row.iter, 0) for row in self]
        for name, _ in self.settings.items('imports'):
            if name not in existing:
                self.settings.remove_option('imports', name)
