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
from feat.common import decorator

from feattool.interfaces import *


_components = dict()


@decorator.simple_class
def register(component):
    component = IGuiComponent(component)
    if component.name is None:
        raise AttributeError('%r has None as name' % (component, ))
    if component.name in _components:
        raise AttributeError(
            'Component with name %s already registered, pointing to %r' %
            (component.name, _components[component.name], ))

    _components[component.name] = component


def query(name):
    return _components.get(name, None)


def get_all():
    return _components.values()
