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
from zope.interface import implements, Interface
from twisted.python import components

from feat.agents.base import resource, agent, partners, descriptor
from feat.agencies import agency, protocols
from feat.common import enum
from feat.common.container import ExpDict


class IGuiState(Interface):
    """
    Interface to parse the agent state
    """

    def get_name(self):
        """ Parent name """

    def iter_elements(self):
        """ Get next element to append """


class GuiState(object):

    implements(IGuiState)

    def __init__(self, obj):
        self.obj = obj

    def get_name():
        return None

    def iter_elements(self):
        return list().__iter__()


class EnumState(GuiState):

    def iter_elements(self):
        yield (None, ('value', self.obj.name), )


class AgentGuiState(GuiState):

    def __init__(self, agent):
        GuiState.__init__(self, agent)

    def get_name(self):
        return [type(self.obj), None]

    def iter_elements(self):
        state = self.obj._get_state()
        for attr in state.__dict__:
            yield (attr, getattr(state, attr))


class ResourcesGuiState(GuiState):

    def __init__(self, resources):
        GuiState.__init__(self, resources)

    def get_name(self):
        return ['resources', None]

    def iter_elements(self):
        state = self.obj._get_state()
        yield (None, ('id_autoincrement', state.id_autoincrement))
        yield 'modifications', state.modifications
        yield 'totals', state.totals


class PartnersGuiState(GuiState):

    def __init__(self, partners):
        GuiState.__init__(self, partners)

    def get_name(self):
        return ['partners', None]

    def iter_elements(self):
        state = self.obj._get_state()
        yield (None, ('agent', type(state.agent)))


class InterestGuiState(GuiState):

    def __init__(self, interest):
        GuiState.__init__(self, interest)

    def get_name(self):
        return ['interest', None]

    def iter_elements(self):
        yield (None, ('factory', self.obj.factory))
        yield (None, ('lobby binding',
                      self.obj._lobby_binding is not None))


class DescriptorGuiState(GuiState):

    def __init__(self, descriptor):
        GuiState.__init__(self, descriptor)

    def get_name(self):
        return ['descriptor', None]

    def iter_elements(self):
        for attr in ['rev', 'doc_id', 'shard']:
            yield (None, (attr, getattr(self.obj, attr)))
        yield ('partners', getattr(self.obj, 'partners'))
        yield ('allocations', getattr(self.obj, 'allocations'))


class TupleGui(GuiState):

    def __init__(self, tup):
        GuiState.__init__(self, tup)

    def get_name(self):
        return ['%s' % self.obj[0],
                '%s' % self.obj[1]]


class ListGui(GuiState):

    def __init__(self, l):
        GuiState.__init__(self, l)

    def iter_elements(self):
        for item, index in zip(self.obj, range(len(self.obj))):
            if isinstance(item, partners.BasePartner):
                yield (None, (index+1, item.__class__))
            else:
                yield (None, (index+1, item))


class DictGui(GuiState):

    def __init__(self, dic):
        GuiState.__init__(self, dic)

    def iter_elements(self):
        for item in self.obj.iteritems():
            yield (None, (item))


components.registerAdapter(
        AgentGuiState,
        agent.BaseAgent,
        IGuiState)


components.registerAdapter(
        EnumState,
        enum.Enum,
        IGuiState)

components.registerAdapter(
        ResourcesGuiState,
        resource.Resources,
        IGuiState)


components.registerAdapter(
        PartnersGuiState,
        partners.Partners,
        IGuiState)


components.registerAdapter(
        DescriptorGuiState,
        descriptor.Descriptor,
        IGuiState)


components.registerAdapter(
        InterestGuiState,
        protocols.BaseInterest,
        IGuiState)


components.registerAdapter(
        DictGui,
        dict,
        IGuiState)

components.registerAdapter(
        DictGui,
        ExpDict,
        IGuiState)

components.registerAdapter(
        ListGui,
        list,
        IGuiState)


components.registerAdapter(
        TupleGui,
        tuple,
        IGuiState)
