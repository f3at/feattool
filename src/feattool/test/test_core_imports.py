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
import tempfile

from feat.test import common
from feat.common import text_helper

from feattool.core import imports, settings


class ImportsTest(common.TestCase):

    def setUp(self):
        self.tempfile = tempfile.mktemp()
        config = text_helper.format_block("""
        [imports]
        feat.everything = True
        """)
        with open(self.tempfile, 'w') as f:
            f.write(config)

        self.settings = settings.SettingsManager(self.tempfile)
        self.imports = imports.Imports(self, self.settings)
        self.imports.load_from_settings()

    def testLoadSettings(self):
        iter = self.imports.get_iter_first()
        self.failIf(iter is None)
        canonical_name, auto = self.imports._parse_row(iter)
        self.assertEqual('feat.everything', canonical_name)
        self.assertTrue(auto)

    def testStoring(self):
        self.imports.append(('flt.everything', False, ))
        val = self.settings.get('imports', 'flt.everything')
        self.assertEqual(val, False)

    def testRemoving(self):
        iter = self.imports.get_iter_first()
        self.failIf(iter is None)
        self.imports.remove(iter)
        self.assertRaises(settings.NoOptionError,
                          self.settings.get, 'imports', 'feat.everything')

    def testEditing(self):
        iter = self.imports.get_iter_first()
        self.failIf(iter is None)
        self.imports.set(iter, 1, False)
        val = self.settings.get('imports', 'feat.everything')
        self.assertFalse(val)

    def testImporting(self):
        self.imports.perform_imports()

    def tearDown(self):
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
