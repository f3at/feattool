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
import re


class HelpAgent(object):

    def __init__(self, parent):
        self.builder = gtk.Builder()
        self.builder.add_from_file('data/ui/help-agent.ui')

        self.window = self.builder.get_object('help_agent_dialog')
        self.window.set_transient_for(parent)
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.window.connect('delete-event', lambda *e: self.close())

        self.close_button = self.builder.get_object('close_button')
        self.close_button.connect('clicked', lambda *e: self.close())

        self.model = self.builder.get_object('model')

    def close(self):
        self.window.hide()
        self.window.destroy()

    def add_help(self, msg):
        self.model.clear()
        items = [re.sub('\s{2,}', '\t', i).split('\t')
                for i in msg.split('\n')]
        for item in items:
            self.model.append(item)

    def run(self):
        self.window.show_all()
