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
import time
import pprint
import gobject
import gtksourceview2
import os
import gtk
import inspect

from zope.interface import classProvides

from feat import everything
from feat.common import log, defer, reflect, error
from feat.agencies import journaler, replay
from feat.agents.base.agent import registry_lookup
from feat.agents.base.replay import resolve_function

from feattool.core import component
from feattool.gui import journal, hamsterball

from feat.interface.log import LogLevel

from feattool.interfaces import IGuiComponent


class AgentsStore(gtk.ListStore):

    def __init__(self):
        gtk.ListStore.__init__(self, str, bool, int, gobject.TYPE_PYOBJECT,
                               str)

    def identify_agent(self, agent_id, agent_name):
        for row in self:
            if row[0] == agent_id:
                row[4] = agent_name

    def get_selected_history(self):
        for row in self:
            if row[1]:
                return row[3]


class LogsStore(gtk.ListStore):

    def __init__(self):
        # message, timestamp, file_path, level, category, log_name, line_num
        gtk.ListStore.__init__(self, str, int, str, str, str, str, int)

    def parse_result(self, result):
        '''
        result should be list of tuples with the format:
        (message, timestamp, category, log_name, file_path, line_num,
        timestamp), which is the result of SqliteWriter.get_log_entries.
        '''
        self.clear()
        for row in result:
            message = row['message']
            level = row['level']
            category = row['category']
            log_name = row['log_name']
            file_path = row['file_path']
            line_num = row['line_num']
            timestamp = row['timestamp']

            self.append((message, timestamp, file_path,
                         LogLevel[level].name, category, log_name, line_num))


class FiltersStore(gtk.ListStore):

    def __init__(self):
        # category, log_name, level, hostname
        gtk.ListStore.__init__(self, str, str, str, gobject.TYPE_INT)

    def get_filters_for_query(self):
        resp = list()
        for row in self:
            if row[3] is None:
                continue
            row_res = dict(level=row[3])
            if row[0] is not None:
                row_res['hostname'] = row[0]
            if row[1] is not None:
                row_res['category'] = row[1]
            if row[2] is not None:
                row_res['name'] = row[2]
            resp.append(row_res)
        return resp


class LogCategoriesStore(gtk.ListStore):

    def __init__(self):
        gtk.ListStore.__init__(self, str, gtk.ListStore)

    def get_log_names_for(self, category):
        for row in self:
            if row[0] == category:
                return row[1]


class LogHostnamesStore(gtk.ListStore):

    def __init__(self):
        gtk.ListStore.__init__(self, str, LogCategoriesStore)

    def get_categories_for(self, hostname):
        for row in self:
            if row[0] == hostname:
                return row[1]


class EntryDetails(gtk.TreeStore):

    def __init__(self):
        gtk.TreeStore.__init__(self, str, str)

        self.iter = None
        self.model = None
        self.function = None

    def get_function(self):
        return self.function

    def _handle_special_entry(self):
        fun_id = self._get_value(2)
        handler_name = "_handle_%s" % (fun_id, )
        method = getattr(self, handler_name, None)
        if not callable(method):
            self._append_row(None, '',
                       "This entry is special, it doesn't have python code.")
        else:
            method()

    def _handle_protocol_created(self):
        params = self._get_value(5)
        factory = params[0]
        self._append_row(None, 'factory', factory)

        if len(params) > 1:
            args = params[2:]
        else:
            args = None
        if args:
            row = self._append_row(None, 'args', None)
            self._render_list(row, args)

        kwargs = self._get_value(6)
        if kwargs:
            row = self._append_row(None, 'keywords', None)
            self._render_dict(row, kwargs)

    def _handle_agent_created(self):
        params = self._get_value(5)
        factory = params[0]
        self._append_row(None, 'factory', factory)

    def _handle_protocol_deleted(self):
        self._append_row(None, '', "This entry doesn't contain information "
                         "on its own, it is usefull only during the replay.")

    def _disabled_entry(self):
        self._append_row(None, '', "This entry couldn't have been replayed, "
                         "because we don't have an agent in hamsterball at "
                         "this point. Entry needs to be preceded by "
                         "'agent_created' or 'snapshot' entry.")

    def parse(self, iter, model):
        self.iter = iter
        self.model = model

        self.clear()
        self.function = None

        if not self._get_value(11):
            self._disabled_entry()
            return

        function_id = self._get_value(2)
        try:
            fun_id, function = resolve_function(function_id, None)
        except AttributeError:
            self._handle_special_entry()
            return
        else:
            if hasattr(function, 'original_func'):
                function = function.original_func
            args = self._get_value(5)
            kwargs = self._get_value(6)
            result = self._get_value(8)
            self._append_function_call(None, function, args, kwargs, result)
            self.function = function

        side_effects = self._get_value(7)
        if side_effects:
            row = self._append_row(None, 'side_effects', None)
            for sfx in side_effects:
                fun_id, args, kwargs, _, result = sfx
                try:
                    function = reflect.named_function(fun_id)
                except ValueError:

                    def unknown_function(*unknown_mimicry):
                        pass

                    unknown_function.__name__ = fun_id
                    function = unknown_function
                self._append_function_call(row, function, args, kwargs, result)

        self._append_row(None, 'fiber_depth', self._get_value(4))
        timestamp = time.strftime("%b %d %Y %H:%M:%S",
                                  time.localtime(float(self._get_value(9))))
        self._append_row(None, 'timestamp', timestamp)
        self._append_row(None, 'journal id', self._get_value(1))
        error_ = self._get_value(12)
        if error_:
            self._append_row(None, 'error', error_)

    def _append_row(self, parent, key, value):
        row = self.append(parent, (key, value, ))
        return row

    def _get_value(self, index):
        return self.model.get_value(self.iter, index)

    def _render_list(self, parent, llist):
        for value, index in zip(llist, range(len(llist))):
            self._append_row(parent, index, pprint.pformat(value))

    def _render_dict(self, parent, ddict):
        for key, value in ddict.iteritems():
            self._append_row(parent, key, pprint.pformat(value))

    def _append_function_call(self, parent, function, args, kwargs, result):
        args = args and list(args) or list()
        kwargs = kwargs or dict()

        argspec = inspect.getargspec(function)
        defaults = argspec.defaults and list(argspec.defaults)
        text = reflect.formatted_function_name(function)

        call_row = self._append_row(parent, 'call', text)
        row = self._append_row(call_row, 'input', None)
        for arg in argspec.args:
            value = None
            try:
                value = args.pop(0)
            except IndexError:
                value = defaults and defaults.pop(0)
            self._append_row(row, arg, repr(value))
        if args:
            self._render_list(row, args)
        self._render_dict(row, kwargs)
        self._append_row(call_row, 'output', pprint.pformat(result))


@component.register
class JournalComponent(log.LogProxy, log.Logger):
    classProvides(IGuiComponent)

    def __init__(self, main):
        log.Logger.__init__(self, main)
        log.LogProxy.__init__(self, main)

        self.main = main
        self._reader = None

        self.je_store = gtk.ListStore(
            str, str, str, str, str, gobject.TYPE_PYOBJECT,
            gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
            gobject.TYPE_PYOBJECT, str, gobject.TYPE_PYOBJECT,
            bool, gobject.TYPE_PYOBJECT)

        self.agents_store = AgentsStore()
        self.details_store = EntryDetails()
        self.source_buffer = gtksourceview2.Buffer()
        self.hamsterball = hamsterball.Model()
        self.logs_store = LogsStore()
        self.filters_store = FiltersStore()
        self.log_hostnames = LogHostnamesStore()

        manager = gtksourceview2.LanguageManager()
        lang = manager.get_language('python')
        self.source_buffer.set_language(lang)

        self.controller = journal.Controller(
            self, self.je_store, self.agents_store,
            self.details_store, self.source_buffer,
            self.hamsterball, self.logs_store,
            self.filters_store, self.log_hostnames)

    def finished(self):
        '''
        Called after the journal viewer window has been closed.
        '''
        self.main.finished()

    ### IGuiComponent ###

    name = 'journal'

    @classmethod
    def construct_window(cls, main_model):
        instance = cls(main_model)
        return instance

    @classmethod
    def get_menu_presentation(cls):
        button = gtk.Button(label='Journal analizer')
        return button

    ### Called by controller ###

    def load_jourfile(self, filename):
        if not os.path.exists(filename):
            raise RuntimeError("File %r doesn't exist!" % (filename, ))
        reader = journaler.SqliteWriter(self, filename=filename)
        return self._initiate_reader(reader)

    def postgres_connect(self, cred):
        self.log("postgres_connect() called with credentials %r")
        reader = journaler.PostgresReader(
            self,
            host=cred.get('host', 'localhost'),
            database=cred['database'],
            user=cred['user'],
            password=cred['password'])
        return self._initiate_reader(reader)

    def _initiate_reader(self, reader):
        old_reader = self._reader
        self._reader = reader
        d = defer.succeed(None)
        if old_reader:
            d.addCallback(defer.drop_param, reader.close)
        d.addCallback(defer.drop_param, self._reader.initiate)
        d.addCallback(defer.drop_param, self._reader.get_histories)
        d.addCallback(self._got_histories)
        d.addCallback(defer.drop_param, self._load_log_data)
        d.addErrback(self._connect_error_handler)
        return d

    def _connect_error_handler(self, fail):
        self._reader = None
        error.handle_failure(self, fail, "Failed connecting.")
        msg = error.get_failure_message(fail)
        self.controller.display_error(msg)

    @defer.inlineCallbacks
    def _load_log_data(self):
        jour = self._reader
        if jour is None:
            return

        self.log_hostnames.clear()

        hostnames = yield jour.get_log_hostnames()
        for hostname in [None] + hostnames:
            categories_store = yield self._load_log_categories(hostname)
            self.log_hostnames.append((hostname, categories_store))

        boundaries = yield jour.get_log_time_boundaries()
        if boundaries:
            start, end = boundaries
            self.controller.log_start_date.set_current(start)
            self.controller.set_start_date(start)
            self.controller.log_end_date.set_current(end)

    @defer.inlineCallbacks
    def _load_log_categories(self, hostname):
        jour = self._reader

        log_categories = LogCategoriesStore()
        log_categories.append()
        categories = yield jour.get_log_categories(hostname=hostname)
        for category in categories:
            names = yield jour.get_log_names(category)
            names_store = gtk.ListStore(str)
            names_store.append()
            for name in names:
                names_store.append((name, ))
                if registry_lookup(category):
                    self.agents_store.identify_agent(name, category)
            log_categories.append((category, names_store))
        defer.returnValue(log_categories)

    @defer.inlineCallbacks
    def query_log(self):
        start_date = self.controller.log_start_date.get_current()
        end_date = self.controller.log_end_date.get_current()

        if self._reader is None:
            return
        self.logs_store.clear()
        logs = yield self._reader.get_log_entries(
            start_date=start_date or None,
            end_date=end_date or None,
            filters=self.filters_store.get_filters_for_query())
        self.logs_store.parse_result(logs)

    def show_journal(self):
        self.details_store.clear()
        self.source_buffer.set_text('')
        history = self.agents_store.get_selected_history()
        if history:
            return self._show_history(history)
        else:
            self.je_store.clear()

    def _show_history(self, history):
        d = defer.succeed(None)
        d.addCallback(defer.drop_result,
                      self._reader.get_entries, history,
                      start_date=self.controller.get_start_date(),
                      limit=self.controller.get_limit())
        d.addCallback(self._parse_history, history.agent_id)
        return d

    def parse_details_for(self, iter):
        '''
        @param iter: TreeIter point to the row in self.je_store to be displayed
        '''
        self.hamsterball.clear()

        self.details_store.parse(iter, self.je_store)
        func = self.details_store.get_function()
        source = func and inspect.getsource(func) or ''
        self.source_buffer.set_text(source)

        enabled = self.je_store[iter][11]
        if enabled:
            registry = self.je_store[iter][10]
            self.hamsterball.append_iter(registry.iteritems())
            self.controller.select_hamsterball(self.je_store[iter][1])

    def clear_all(self):
        self.agents_store.clear()
        self.je_store.clear()
        self.details_store.clear()
        self.source_buffer.set_text('')
        self.hamsterball.clear()
        self.logs_store.clear()
        self.filters_store.clear()
        self.log_hostnames.clear()

    ### private ###

    def _got_histories(self, histories):
        self.clear_all()
        for history in histories:
            row = self.agents_store.append()
            self.agents_store.set(row, 0, history.agent_id)
            self.agents_store.set(row, 1, False)
            self.agents_store.set(row, 2, history.instance_id)
            self.agents_store.set(row, 3, history)
            self.agents_store.set(row, 4, 'unknown yet')

    def _parse_history(self, history, agent_id):
        self.je_store.clear()
        self.info('Reading %r entries.', len(history))
        rep = replay.Replay(iter(history), agent_id,
                            inject_dummy_externals=True)
        try:
            for entry in rep:
                try:
                    entry.apply()
                    enabled = True
                    error = None
                except replay.ReplayError as e:
                    msg = ("Encountered problem while replaying: \n %s" % e)
                    self.controller.display_error(msg)
                    error = e
                except replay.NoHamsterballError:
                    error = None
                    enabled = False
                row = self.je_store.append()
                self.je_store.set(row, 0, entry.agent_id)
                self.je_store.set(row, 1, str(entry.journal_id))
                self.je_store.set(row, 2, entry.function_id)
                self.je_store.set(row, 3, entry.fiber_id)
                self.je_store.set(row, 4, entry.fiber_depth)
                args, kwargs = entry.get_arguments()
                self.je_store.set(row, 5, args)
                self.je_store.set(row, 6, kwargs)
                if enabled:
                    sfx = map(lambda row: self._parse_sfx(row, entry, rep),
                              entry._side_effects)
                    self.je_store.set(row, 7, sfx)
                self.je_store.set(row, 8, entry.result)
                self.je_store.set(row, 9, entry._timestamp)
                if enabled:
                    self.je_store.set(row, 10, rep.snapshot_registry())
                self.je_store.set(row, 11, enabled)
                self.je_store.set(row, 12, error)
            agent_type = rep.get_agent_type()
            if agent_type:
                self.agents_store.identify_agent(agent_id, agent_type)
        except TypeError as e:
            self.je_store.clear()
            msg = ("Journal import failed. \nProbably you are missing some "
                   "module. \nError message: \n%s" % (str(e), ))
            self.controller.display_error(msg)
        if len(self.je_store) > 0:
            self.controller.set_end_date(self.je_store[-1][9])

    def _parse_sfx(self, row, journal_entry, rep):
        sfx = list(journal_entry.restore_side_effect(row, parse_args=True))
        sfx[4] = rep.unserializer.convert(sfx[4])
        return sfx
