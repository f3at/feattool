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

from feat.agents.base import agent
from feat.common import log

from feattool.core import guistate, settings


class AgentInfo(object):
    """ Show information about selected agent """

    def __init__(self, builder):
        self.builder = builder
        self.model = gtk.TreeStore(str, str)
        self.view = self.builder.get_object('agent_state_view')
        self.view.set_model(self.model)

        self._setup_columns()

    def clear(self):
        self.model.clear()

    def _setup_columns(self):
        columns = self.view.get_columns()
        for col in columns:
            col.connect('notify::width', self.set_column_width)
            name = 'gui/col_width_%s' % (col.get_title())
            width = settings.get_int_option(name, 200)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            col.set_resizable(True)
            col.set_fixed_width(width)

    def set_column_width(self, col, *e):
        name = 'gui/col_width_%s' % (col.get_title())
        w = col.get_width()
        if w != settings.get_int_option(name, -1):
            settings.set_option(name, w)

    def load(self, obj, parent, name=None):
        try:
            parse = guistate.IGuiState(obj)
            if name is None:
                name = parse.get_name()
            else:
                name = [name, None]
            node = self.model.append(parent, name)
            for e in parse.iter_elements():
                self.load(e[1], node, e[0])
            self.view.expand_row(self.model.get_path(node), True)
        except TypeError as e:
            log.info('agent-info', 'Error adapting: %r', e)
