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
import os
from ConfigParser import (
        RawConfigParser,
        NoSectionError,
        NoOptionError)

import glib

manager = None


class SettingsManager(RawConfigParser):

    def __init__(self, path=None):
        RawConfigParser.__init__(self)

        if path:
            self.location = path
        else:
            config_home = glib.get_user_config_dir()
            config_home = os.path.join(config_home, 'feattool')
            if not os.path.exists(config_home):
                os.makedirs(config_home)
            self.location = os.path.join(config_home, 'settings.ini')

        if not os.path.exists(self.location):
            open(self.location, "w").close()

        self._dirty = False
        self._saving = False

        try:
            self.read(self.location)
        except:
            pass

       #Save settings every 30 secs
        glib.timeout_add_seconds(30, self._timeout_save)

    def _timeout_save(self):
        self.save()
        return True

    def set(self, section, options, value):
        r = RawConfigParser.set(self, section, options, value)
        self._dirty = True
        return r

    def set_option(self, option, value):
        splitvals = option.split('/')
        section, key = "/".join(splitvals[:-1]), splitvals[-1]

        try:
            self.set(section, key, value)
        except NoSectionError:
            self.add_section(section)
            self.set(section, key, value)

    def get_option(self, option, default=None):
        splitvals = option.split('/')
        section, key = "/".join(splitvals[:-1]), splitvals[-1]

        try:
            value = self.get(section, key)
        except NoSectionError:
            value = default
        except NoOptionError:
            value = default
        return value

    def get_int_option(self, option, default=None):
        return int(self.get_option(option, default))

    def save(self):
        if self._saving or not self._dirty:
            return

        self._saving = True
        with open(self.location + '.new', 'w') as f:
            self.write(f)
            f.flush()

        os.rename(self.location + '.new', self.location)
        self._saving = False
        self._dirty = False


manager = SettingsManager()
get_option = manager.get_option
get_int_option = manager.get_int_option
set_option = manager.set_option
