#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='feat-dev',
      version='0.1',
      description='Feat development tools',
      author='Flumotion Developers',
      author_email='coreteam@flumotion.com',
      platforms=['any'],
      package_dir={'': 'src'},
      packages=(find_packages(where='src')),
      scripts=['bin/feattool'],
      package_data={'': ['src/feattool/data/ui/*.ui']},
      include_package_data=True)


