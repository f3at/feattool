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
import datetime

import gtk


class CommandHistory(object):

    def __init__(self, parent, history):
        self.builder = gtk.Builder()
        self.builder.add_from_file('data/ui/command-history.ui')

        self.window = self.builder.get_object('command_history_dialog')
        self.window.set_transient_for(parent)
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.window.connect('delete-event', lambda *e: self.close())

        self.close_button = self.builder.get_object('close_button')
        self.close_button.connect('clicked', lambda *e: self.close())

        self.view = self.builder.get_object('date_view')
        self.view.connect('cursor-changed', self._on_cursor_changed)

        self.model = self.builder.get_object('date_model')

        self.editor = self.builder.get_object('text_view')
        self.buffer = self.editor.get_buffer()
        date_tag = gtk.TextTag('date')
        date_tag.set_property('foreground', 'blue')
        tag_table = self.buffer.get_tag_table()
        tag_table.add(date_tag)

        self.history = history

        self._init()

    def _init(self):
        dates = self.history.load_dates()
        self.model.clear()
        for d in dates:
            self.model.append([d])

    def _on_cursor_changed(self, view):
        self.buffer.set_text('')
        selection = self.view.get_selection()
        (_, paths) = selection.get_selected_rows()
        if not paths:
            return
        iter = self.model.get_iter(paths[0])
        strdate = self.model.get_value(iter, 0)
        date = datetime.datetime.strptime(strdate, '%Y-%m-%d').date()
        cmds = self.history.read_commands(date)
        for d, txt in cmds:
            _, eob = self.buffer.get_bounds()
            self.buffer.insert_with_tags_by_name(eob, str(d), 'date')
            _, eob = self.buffer.get_bounds()
            self.buffer.insert(eob, '\n'+txt+'\n\n')
        return True

    def close(self):
        self.window.hide()
        self.window.destroy()

    def run(self):
        self._init()
        self.window.show_all()
