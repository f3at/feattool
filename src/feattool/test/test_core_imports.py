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
