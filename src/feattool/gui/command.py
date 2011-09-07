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
from feat.common.text_helper import format_block

from feattool.core import history
from feattool.gui.dlg import command_history


class Command(object):
    """
    The command panel
    """

    def __init__(self, window, builder, driver):
        self.builder = builder
        self.window = window

        self.editor = self.builder.get_object('command_editor')
        textbuffer = self.editor.get_buffer()
        textbuffer.set_text(format_block("""
        agency = spawn_agency()
        host_desc = descriptor_factory('host_agent')
        agency.start_agent(host_desc)
        """))

        textbuffer.connect('changed', self.on_text_changed)

        self.run_button = self.builder.get_object('run_button')
        self.run_button.connect('clicked', self.on_run_clicked)

        self.clear_button = self.builder.get_object('clear_button')
        self.clear_button.connect('clicked', self.on_clear_clicked)

        self.history_button = self.builder.get_object('history_button')
        self.history_button.connect('clicked', self.on_history_clicked)

        self.driver = driver
        self.driver.on_processed_callback(self._on_script_processed)

        self.history = history.HistoryLogger()

    def on_run_clicked(self, button):
        textbuffer = self.editor.get_buffer()
        script = textbuffer.get_text(
                textbuffer.get_start_iter(),
                textbuffer.get_end_iter())
        self.driver.process(script)
        #self.run_button.set_sensitive(False)
        self.history.append_command(script)

    def _on_script_processed(self):
        if self.run_button.get_sensitive() == False:
            self.run_button.set_sensitive(True)

    def on_clear_clicked(self, button):
        textbuffer = self.editor.get_buffer()
        textbuffer.set_text('')

    def on_text_changed(self, textbuffer):
        count = textbuffer.get_char_count()
        self.run_button.set_sensitive(count)
        self.clear_button.set_sensitive(count)

    def on_history_clicked(self, button):
        self.history_dlg = command_history.CommandHistory(
                self.window,
                self.history)
        self.history_dlg.run()
