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


class Error(object):

    def __init__(self, builder, driver):
        self.builder = builder

        self.model = self.builder.get_object('error_model')
        self.label = self.builder.get_object('error_tab')

        self.driver = driver
        self.driver.on_processed_callback(self._on_script_processed)

    def _on_script_processed(self):
        error = self.driver.get_error()
        if error:
            self.label.set_markup('<span color="red">%s</span>' % (
                self.label.get_text()))
            self.model.append([error])
        else:
            self.label.set_markup('<span>%s</span>' % (
                self.label.get_text()))
            self.model.clear()
