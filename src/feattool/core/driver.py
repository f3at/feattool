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
import glib
import pydot

from feat.simulation import driver
from feat.common import manhole, defer

from feat import applications


class GuiParser(manhole.Parser):

    def __init__(self, drv, output, commands, cb_on_finish=None):
        manhole.Parser.__init__(self, drv, output, commands, cb_on_finish)
        self.driver = drv

    def _error_handler(self, f):
        self.driver._set_error(f.getErrorMessage())
        manhole.Parser._error_handler(self, f)


class GuiDriver(driver.Driver):

    def __init__(self):
        driver.Driver.__init__(self)
        self.callbacks = []
        self._parser = GuiParser(
                self,
                self._output,
                self,
                self.finished_processing)

        self.last_error = ''
        self.current_dot = ''

        self.filter_id = []
        self.filter_type = []

        self.next_update = 2000
        self.min_update = 15000
        self.timer = glib.timeout_add(self.next_update/2, self._timeout_dot)

    def finished_processing(self):
        if self.timer:
            glib.source_remove(self.timer)
            self.timer = 0
        self._timeout_dot()

    def _throw_callbacks(self):
        for callback in self.callbacks:
            callback()

    def _timeout_dot(self):
        self._update_agent_filter()
        dot = export_drv_to_dot(self, self.filter_id)
        if self.current_dot != dot:
            self.current_dot = dot
            self._throw_callbacks()
            self.next_update = self.next_update/2
        else:
            self.next_update = round(self.next_update * 1.05)
        if self.next_update < 2000:
            self.next_update = 2000
        if self.next_update > self.min_update:
            self.next_update = self.min_update
        self.timer = glib.timeout_add(int(self.next_update), self._timeout_dot)
        return False

    def add_filter(self, type_):
        if type_ not in self.filter_type:
            self.filter_type.append(type_)

    def remove_filter(self, type_):
        if type_ in self.filter_type:
            self.filter_type.remove(type_)

    def _update_agent_filter(self):
        agent_objects = [applications.lookup_agent(t)
                         for t in self.filter_type]
        self.filter_id = []

        def is_in_filter(aa):
            return type(aa.get_agent()) in agent_objects

        for agency in self._agencies:
            self.filter_id += [x.get_agent_id()
                               for x in agency._agents
                               if is_in_filter(x)]

    def on_processed_callback(self, callback):
        self.callbacks.append(callback)

    def _set_error(self, msg):
        self.last_error = msg

    def get_error(self):
        return self.last_error

    def export_to_dot(self):
        return self.current_dot

    def clear(self):
        agents = []
        for ag in self._agencies:
            for a in ag._agents:
                agents.append(a)
        d = defer.DeferredList([a._terminate() for a in agents])
        d.addCallback(lambda _: self._remove_agencies())
        d.addCallback(lambda _: self.finished_processing())
        return d

    def _remove_agencies(self):
        while len(self._agencies):
            del self._agencies[0]


def export_drv_to_dot(drv, agent_list=[]):
    shards = {}
    edges = []

    cluster_count = 0
    agency_count = 1

    graph = pydot.Graph()
    for agency in drv._agencies:
        agency_name = 'agency %d' %(agency_count)
        agency_dot = pydot.Subgraph(
            graph_name = 'cluster_%d' %(cluster_count),
            label = agency_name,
            style="filled",
            color="lightyellow")
        cluster_count += 1
        agency_count += 1
        agency_added = False
        for agent in agency._agents:
            desc = agent.get_descriptor()
            if desc.doc_id in agent_list:
                continue

            shard_name = desc.shard
            if shard_name in shards:
                shard_dot = shards[shard_name]
            else:
                shard_dot = pydot.Subgraph(
                        graph_name='cluster_%d' % (cluster_count),
                        style='filled',
                        color='lightblue',
                        label=shard_name)
                shards[shard_name] = shard_dot
                graph.add_subgraph(shard_dot)
                cluster_count += 1
            if not agency_added:
                shard_dot.add_subgraph(agency_dot)
                agency_added = True
            node = pydot.Node(
                    name=str(desc.doc_id),
                    label=type(agent.get_agent()).__name__,
                    color="white",
                    style="filled",
                    URL='%s' % (desc.doc_id))
            agency_dot.add_node(node)
            for p in desc.partners:
                dst = p.recipient.key
                src = desc.doc_id
                if dst not in agent_list and \
                    (src, dst) not in edges and \
                    (dst, src) not in edges:
                        edges.append((src, dst))

    #Finnaly add the edges to graph
    for e in edges:
        edge = pydot.Edge(src=e[0], dst=e[1])
        graph.add_edge(edge)
    return graph.to_string()
