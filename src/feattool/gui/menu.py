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
import gobject
import gtk
import gettext
_ = gettext.gettext


class Menu(gtk.Menu):

    def __init__(self):
        gtk.Menu.__init__(self)

    def append(self, text, callback, stock_id=None):
        if stock_id:
            item = gtk.ImageMenuItem(text)
            image = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_MENU)
            item.set_image(image)
        else:
            item = gtk.MenuItem(text)
        item.connect('activate', lambda *e: callback())
        gtk.Menu.append(self, item)

    def popup(self, event):
        gtk.Menu.show_all(self)
        gtk.Menu.popup(self, None, None, None, event.button, event.time)


class AgentMenu(Menu, gobject.GObject):

    __gsignals__ = {
            'terminate-agent': (gobject.SIGNAL_RUN_LAST, None,
                (gobject.TYPE_STRING, )),
            'help-agent': (gobject.SIGNAL_RUN_LAST, None,
                (gobject.TYPE_STRING, ))}

    def __init__(self, agent_id):
        Menu.__init__(self)

        self.append(_('Exposed methods'), self.on_help_agent, gtk.STOCK_HELP)
        gtk.Menu.append(self, gtk.SeparatorMenuItem())
        self.append(_('Terminate'), self.on_terminate_agent, gtk.STOCK_DELETE)
        self.agent_id = agent_id

    def on_terminate_agent(self):
        self.emit('terminate-agent', self.agent_id)

    def on_help_agent(self):
        self.emit('help-agent', self.agent_id)
