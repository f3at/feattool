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
import time
import pango
import gtksourceview2
import gobject
import gtk

from twisted.internet import reactor

from feat.common import log, first, run
from feat.extern.log import log as xlog

from feattool import data
from feattool.gui import hamsterball, date, terminal
from feattool.core import settings

from feat.interface.log import LogLevel

class colors:
    reset = '\033[0m'
    default = '\033[2;37;40m'
    where = '\033[1;30;40m'
    levels = {"LOG": '\033[1;30;40m',
              "DEBUG": '\033[2;37;40m',
              "INFO": '\033[1;37;40m',
              "WARN": '\033[1;33;40m',
              "ERROR": '\033[1;31;40m'}


class Controller(log.Logger, log.LogProxy):
    """
    This is the controller of journal viewer component.
    """

    def __init__(self, model, journal_entries, agent_list,
                 entry_details, code_preview, hamsterball,
                 logs_store, filters_store, log_hostnames):
        log.Logger.__init__(self, model)
        log.LogProxy.__init__(self, model)

        self.model = model

        self.builder = gtk.Builder()
        self.builder.add_from_file(data.path('ui', 'main.ui'))
        self.builder.add_from_file(data.path('ui', 'journal-viewer.ui'))

        self.view = MainWindow(self, self.builder,
                               journal_entries, agent_list,
                               entry_details, code_preview, hamsterball,
                               logs_store, filters_store, log_hostnames)
        self.view.show()

        self._start_date = date.DateField(
            input=self.builder.get_object('start_date'),
            button=self.builder.get_object('pick_date'),
            set_cb=self.set_start_date,
            parent=self.view.window)
        self.log_start_date = date.DateField(
            input=self.builder.get_object('log_start_date'),
            button=self.builder.get_object('pick_log_start_date'),
            parent=self.view.window)
        self.log_end_date = date.DateField(
            input=self.builder.get_object('log_end_date'),
            button=self.builder.get_object('pick_log_end_date'),
            parent=self.view.window)
        self._end_date = None
        self._limit = 0

        self._configure_limit()

    def quit(self):
        self.model.finished()

    def _configure_limit(self):
        if not settings.manager.has_section('journal'):
            settings.manager.add_section('journal')
        limit = first(v for k, v in settings.manager.items('journal')
                      if k == 'limit') or 500
        limit = int(limit)

        obj = self.builder.get_object('limit')
        obj.configure(gtk.Adjustment(limit, 0, 10000, 100), 0, 0)
        obj.set_wrap(True)
        obj.connect('changed', self._limit_changed)
        self.set_limit(limit)

    def _limit_changed(self, obj):
        self.set_limit(obj.get_text())

    def set_limit(self, limit):
        self._limit = int(limit)
        settings.manager.set('journal', 'limit', int(limit))
        settings.manager.save()

    def get_limit(self):
        return self._limit

    def set_start_end(self):
        if self._end_date:
            self.set_start_date(self._end_date)

    def set_start_date(self, epoc):
        self._start_date.set_current(epoc)
        self.show_journal()

    def get_start_date(self):
        return self._start_date.get_current()

    def set_end_date(self, epoc):
        self._end_date = epoc
        obj = self.builder.get_object('end_date')
        timestamp = time.strftime("%b %d %Y %H:%M:%S",
                                  time.localtime(float(self._end_date)))
        obj.set_text(timestamp)
    ### called by view ###

    def choose_jourfile(self):
        filechooser = gtk.FileChooserDialog(
            title='Choose journal file',
            parent=self.view.window,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filechooser.connect('response', self._choose_jourfile_response)
        filechooser.show_all()

    def choose_postgres(self):
        chooser = ChoosePostgres(self.view.window)
        chooser.connect('response', self._choose_postgres_response)
        chooser.show_all()

    def refresh_journaler(self):
        self.model.refresh_journaler()

    def open_imports_manager(self):
        self.model.main.show_imports_manager()

    def show_journal(self):
        self.model.show_journal()

    def show_entry_details(self, iter):
        self.model.parse_details_for(iter)

    def add_filter(self):
        self.view.filters_store.append((None, None, None, 5))

    def remove_filter(self):
        path, focus = self.view.filter_list.get_cursor()
        if path:
            iter = self.view.filters_store.get_iter(path)
            del(self.view.filters_store[iter])

    def query_log(self):
        self.model.query_log()

    ### called by model ###

    def display_error(self, msg):
        dialog = gtk.Dialog("Error", self.view.window,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, ))
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_size_request(850, 600)
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scrolledwindow.set_border_width(10)
        scrolledwindow.show_all()
        label = gtk.Label(msg)
        label.set_property('width-chars', 100)
        label.set_property('wrap', True)
        scrolledwindow.add_with_viewport(label)
        dialog.vbox.pack_start(scrolledwindow)
        dialog.show_all()

        def destroy(dial, resp):
            dial.destroy()

        dialog.connect('response', destroy)

    def select_hamsterball(self, journal_id):
        self.view.select_hamsterball(journal_id)

    ### private ###

    def _choose_jourfile_response(self, dialog, response_id):
        selected = dialog.get_filenames()
        dialog.destroy()
        if response_id == gtk.RESPONSE_OK:
            self.model.load_jourfile(selected[0])

    def _choose_postgres_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_OK:
            credentials = dialog.get_credentials()
            self.model.postgres_connect(credentials)
        dialog.destroy()


class ChoosePostgres(gtk.Dialog):

    def __init__(self, parent):
        gtk.Dialog.__init__(self, "Choose postgres server", parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fields = [('host', ''), ('database', 'feat'),
                  ('user', ''), ('password', '')]
        self._entries = dict()
        for name, default in fields:
            hbox = gtk.HBox()
            self.vbox.pack_start(hbox)
            label = gtk.Label("%s: " % (name.capitalize(), ))
            label.set_width_chars(12)
            hbox.pack_start(label)
            field = gtk.Entry()
            field.set_text(str(default))
            self._entries[name] = field
            hbox.pack_start(field)

    def get_credentials(self):
        return dict([(key, entry.get_text())
                     for key, entry in self._entries.items()])


class MainWindow(log.Logger):
    """
    This is the view of main journal viewer window.
    """

    def __init__(self, controller, builder, journal_entries_store,
                 agents_store, entry_details, code_preview, hamsterball,
                 logs_store, filters_store, log_hostnames):
        log.Logger.__init__(self, controller)

        self.controller = controller
        self.builder = builder

        self.journal_entries_store = journal_entries_store
        self.agents_store = agents_store
        self.entry_details = entry_details
        self.code_preview = code_preview
        self.hamsterball = hamsterball
        self.logs_store = logs_store
        self.filters_store = filters_store
        self.log_hostnames = log_hostnames

        self._setup_window()
        self._setup_menu()
        self._setup_lists()
        self._setup_buttons()

    def _setup_window(self):
        self.window = self.builder.get_object('journal_viewer')
        self.window.set_title('Journal viewer')
        self.window.connect('destroy', self._on_destroy)
        self.window.resize(1200, 1600)
        self.window.maximize()

    def _setup_menu(self):
        action = self.builder.get_object('choose_jourfile')
        action.connect('activate', lambda _: self.controller.choose_jourfile())

        action = self.builder.get_object('postgres_connect')
        action.connect('activate', lambda _: self.controller.choose_postgres())

        action = self.builder.get_object('quit_menuitem')
        action.connect('activate', self._on_destroy)

        action = self.builder.get_object('refresh_journaler')
        action.connect('activate', lambda _: self.controller.refresh_journaler())

        menu = self.builder.get_object('imports_menuitem')
        menu.connect('activate',
                     lambda _: self.controller.open_imports_manager())

    def _setup_lists(self):
        self._setup_agent_list()
        self._setup_journal_entries()
        self._setup_entry_details()
        self._setup_source_preview()
        self._setup_logs_list()
        self._setup_filters_list()
        self._setup_hamsterball()

    def _setup_buttons(self):
        clear = self.builder.get_object('clear_search')
        search = self.builder.get_object('je_search')
        clear.connect('clicked', lambda *_: search.set_text(''))
        but = self.builder.get_object('set_start_end')
        but.connect('clicked', lambda *_: self.controller.set_start_end())

        but = self.builder.get_object('add_filter')
        but.connect('clicked', lambda *_: self.controller.add_filter())

        but = self.builder.get_object('remove_filter')
        but.connect('clicked', lambda *_: self.controller.remove_filter())

        but = self.builder.get_object('query_log')
        but.connect('clicked', lambda *_: self.controller.query_log())

    def _setup_source_preview(self):
        code_view = gtksourceview2.View(self.code_preview)
        code_view.show_all()
        self.builder.get_object('code_preview').add(code_view)

    def select_hamsterball(self, url):
        self.hamsterball_widget.select(url)

    def _setup_hamsterball(self):
        self.hamsterball_widget = \
                                hamsterball.HamsterballWidget(self.hamsterball)
        self.hamsterball_widget.show_all()
        self.builder.get_object('hamsterball').add_with_viewport(
            self.hamsterball_widget)

    def _setup_agent_list(self):
        agent_list = AgentList(model=self.agents_store)
        agent_list.show_all()
        self.builder.get_object('agents_list').add(agent_list)
        self.agent_list = agent_list

        agent_list.connect('agent-marked',
                           lambda _, iter: self.controller.show_journal())

    def _setup_journal_entries(self):
        search = self.builder.get_object('je_search')
        journal_entries = JournalEntries(model=self.journal_entries_store,
                                         search=search)
        journal_entries.show_all()
        self.builder.get_object('journal_entries').add(journal_entries)

        journal_entries.connect('entry-marked', self._journal_entry_marked)

    def _setup_entry_details(self):
        self.entry_details = EntryDetails(self.entry_details)
        self.entry_details.show_all()
        self.builder.get_object('entry_details').add(self.entry_details)

    def _setup_logs_list(self):
        self.log_list = LogList(self.logs_store)
        self.log_list.show_all()
        self.builder.get_object('logentries').add(self.log_list)

    def _setup_filters_list(self):
        self.filter_list = FilterList(self.filters_store, self.log_hostnames)
        self.filter_list.show_all()
        self.builder.get_object('categories').add(self.filter_list)

    def _journal_entry_marked(self, model, iter):
        self.controller.show_entry_details(iter)
        self.entry_details.expand_all()

    def _on_destroy(self, window):
        self.log_list.destroy()
        self.window.hide_all()
        self.controller.quit()

    def show(self):
        self.window.show_all()


class AgentList(gtk.TreeView):

    __gsignals__ = {"agent-marked": (gobject.SIGNAL_RUN_LAST,\
                                     gobject.TYPE_NONE, [gtk.TreeIter])}

    def __init__(self, model=None):
        gtk.TreeView.__init__(self, model)
        self._setup_columns()

    def _setup_columns(self):
        renderer = gtk.CellRendererText()
        toggle_renderer = gtk.CellRendererToggle()
        toggle_renderer.connect('toggled', self._agent_toggle_toggled)
        col = gtk.TreeViewColumn('')
        col.set_min_width(20)
        col.pack_start(toggle_renderer, False)
        col.add_attribute(toggle_renderer, 'active', 1)
        self.append_column(col)

        columns = [('Agent ID', 0),
                   ('I ID', 2),
                   ('Type', 4),
                   ('Hostname', 5)]
        for name, index in columns:
            col = gtk.TreeViewColumn(name)
            col.pack_start(renderer, True)
            col.set_cell_data_func(renderer, self._render_agent_entry, index)
            self.append_column(col)

    def _agent_toggle_toggled(self, cell, path):
        model = self.get_model()
        iter = model.get_iter((int(path), ))
        val = model.get_value(iter, 1)

        def set_false(model, path, iter):
            model.set(iter, 1, False)

        model.foreach(set_false)
        val = not val
        model.set(iter, 1, val)
        param = val and iter or None

        self.emit('agent-marked', param)

    def _render_agent_entry(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('text', value)
        cell.set_property('editable', True)


class JournalEntries(gtk.TreeView):

    __gsignals__ = {"entry-marked": (gobject.SIGNAL_RUN_LAST,\
                                     gobject.TYPE_NONE, [gtk.TreeIter])}

    def __init__(self, model=None, search=None):
        model_f = model.filter_new()
        model_f.set_visible_func(self._je_visible)

        gtk.TreeView.__init__(self, model_f)
        self._selected_fiber_id = None
        self._selected_journal_id = None

        self._search = search
        self._search.connect('changed', lambda *_: model_f.refilter())

        self._setup_columns()
        self.connect('cursor_changed', self._journal_cursor_changed)

    def _setup_columns(self):
        text_renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn('Time')
        col.set_min_width(70)
        col.pack_start(text_renderer, True)
        col.set_cell_data_func(text_renderer, self._render_time)
        self.append_column(col)

        col = gtk.TreeViewColumn('Journal entry')
        col.pack_start(text_renderer, True)
        col.set_cell_data_func(text_renderer, self._render_journal_entry)
        self.append_column(col)

    def _journal_cursor_changed(self, treeview):
        path, focus = treeview.get_cursor()
        model = self.get_model()
        iter = model.get_iter(path)
        child_iter = model.convert_iter_to_child_iter(iter)
        self.emit('entry-marked', child_iter)
        value = model.get_value(iter, 3)
        self._selected_fiber_id = value
        value = model.get_value(iter, 1)
        self._selected_journal_id = value
        self.queue_draw()

    def _render_journal_entry(self, column, cell, model, iter):
        value = model.get_value(iter, 2)
        cell.set_property('text', value)

        cell.set_property('weight-set', True)
        cell.set_property('underline-set', True)
        cell.set_property('editable', True)

        fiber_id = model.get_value(iter, 3)
        if self._selected_fiber_id and self._selected_fiber_id == fiber_id:
            weight = 700
        else:
            weight = 400
        cell.set_property('weight', weight)
        enabled = model.get_value(iter, 11)
        has_error = model.get_value(iter, 12) is not None
        if not enabled:
            color = gtk.gdk.Color(40000, 40000, 40000)
        elif has_error:
            color = gtk.gdk.Color(0xffff, 0, 0)
        else:
            color = gtk.gdk.Color(0, 0, 0)
        cell.set_property('foreground-gdk', color)

        journal_id = model.get_value(iter, 1)
        if self._selected_journal_id and \
               self._selected_journal_id == journal_id:
            underline = pango.UNDERLINE_SINGLE
        else:
            underline = pango.UNDERLINE_NONE
        cell.set_property('underline', underline)

    def _render_time(self, column, cell, model, iter):
        value = model.get_value(iter, 9)
        try:
            year, month, mmday, hour, min, sec, daw, yday, isdst = \
                  time.localtime(float(value))
            formatted = "%s:%s:%s" % (hour, min, sec)
            cell.set_property('text', formatted)
        except TypeError:
            cell.set_property('text', str(value))

    def _je_visible(self, model, iter):
        value = model.get_value(iter, 2)
        key = self._search.get_text()
        return value and key in value


class EntryDetails(gtk.TreeView):

    def __init__(self, model=None):
        gtk.TreeView.__init__(self, model)

        renderer = gtk.CellRendererText()
        columns = ("Detail", "Value")
        for column, index in zip(columns, range(len(columns))):
            col = gtk.TreeViewColumn(column)
            col.set_resizable(True)
            col.set_min_width(140)
            col.pack_start(renderer, True)
            col.set_cell_data_func(renderer, self._render_details, index)
            self.append_column(col)

    def _render_details(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('text', value)
        cell.set_property('editable', True)
        cell.set_property('wrap-width', column.get_property('width'))
        cell.set_property('wrap-mode', pango.WRAP_WORD)


class LogList(terminal.VirtualTerminal):

    def __init__(self, model=None):
        terminal.VirtualTerminal.__init__(self)
        self.model = model
        self.model.connect('full_update', self._update_view)
        self._buffer = '/tmp/feattool_log_widget.tmp'
        if os.path.exists(self._buffer):
            os.remove(self._buffer)
        self._should_restart = True

    def _update_view(self, model):
        self._run_less()

    def _run_less(self):
        if self._pid:
            run.term_pid(self._pid)
        else:
            with file(self._buffer, 'w') as f:
                for (hostname, message, timestamp, file_path, level,
                     category, log_name, line_num) in self.model:
                    self._log_line(hostname, f, level, log_name, category,
                                   file_path, line_num, message, timestamp)
            self.run_command('less -RS %s' % (self._buffer, ))

    def run_command_done_callback(self, term):
        terminal.VirtualTerminal.run_command_done_callback(self, term)
        if self._should_restart:
            self._run_less()

    def destroy(self):
        self._should_restart = False
        if self._pid:
            run.term_pid(self._pid)

    def _shorten(self, s, m):
        if len(s) < m:
            return s
        return s[:((m-3)//2)] + "..." + s[-((m-3)//2)-((m-3)%2):]

    def _log_line(self, hostname, output, level, object,
                  category, file, line, message, timestamp):

        o = ""
        if object:
            o = self._shorten('"' + object + '"', 32)

        if len(hostname) > 14:
            hostname = ".".join(hostname.split('.')[:2])
        if len(hostname) > 14:
            hostname = hostname[:11] + "..."

        where = "(%s:%d)" % (file, line)

        level = level.upper()
        level = _level_lookup.get(level, level)

        color = colors.levels.get(level, colors.default)
        output.write(color)

        # hostname level   pid     object   cat      time
        # 14 + 1 + 5 + 1 + 7 + 1 + 32 + 1 + 17 + 1 + 15 + 1 == 100
        output.write('%-14s %-5s [%5d] %-32s %-17s %-19s ' %
                     (hostname, level,
                      os.getpid(), o, category,
                      time.strftime("%b %d %H:%M:%S",
                                    time.localtime(timestamp))))

        # Padding the message
        parts = message.strip(" \n").split("\n")
        if len(parts) > 1:
            message = parts[0] + "\n"
            message += "\n".join(color+" "*100 + p for p in parts[1:])

        try:
            output.write('%s %s%s\n' % (message, colors.where, where))
        except UnicodeEncodeError:
            # this can happen if message is a unicode object,
            # convert it back into a string using the UTF-8 encoding
            message = message.encode('UTF-8')
            output.write('%s %s\n' % (message, where))


class FilterList(gtk.TreeView):

    def __init__(self, model=None, hostnames=None):
        gtk.TreeView.__init__(self, model)

        self._level_model = gtk.ListStore(gobject.TYPE_STRING,
                                          gobject.TYPE_INT)
        self._hostnames_store = hostnames

        for level in LogLevel:
            self._level_model.append((level.name, int(level)))

        columns = [("Hostname", 150),
                   ("Category", 100),
                   ("Name", 100),
                   ("Level", 40, )]
        for (column, width), index in zip(columns, range(len(columns))):
            renderer = gtk.CellRendererCombo()
            renderer.connect('changed', self._combo_changed, index)
            col = gtk.TreeViewColumn(column)
            col.set_resizable(True)
            col.set_min_width(width)
            col.pack_start(renderer, True)
            col.set_cell_data_func(renderer, self._render, index)
            self.append_column(col)

    def _combo_changed(self, combo, path_string, new_iter, index):
        model = self.get_model()
        if index == 3:
            value = self._level_model[new_iter][1]
        if index in [0, 1, 2]:
            m = combo.get_property('model')
            value = m[new_iter][0]
        if model:
            model[path_string][index] = value

    def _render(self, column, cell, model, iter, index):
        cell.set_property('editable', True)
        cell.set_property('text-column', 0)
        cell.set_property('has-entry', False)

        if index == 3:
            cell.set_property('model', self._level_model)
            lvl = model.get_value(iter, index)
            cell.set_property('text', self._level_model[lvl - 1][0])
        elif index == 0:
            cell.set_property('model', self._hostnames_store)
            cell.set_property('text', model.get_value(iter, index))
        elif index == 1:
            hostname = model.get_value(iter, 0)
            filtered = self._hostnames_store.get_categories_for(hostname)
            cell.set_property('model', filtered)
            cell.set_property('text', model.get_value(iter, index))
        elif index == 2:
            hostname = model.get_value(iter, 0)
            categories = self._hostnames_store.get_categories_for(hostname)
            cat = model.get_value(iter, 1)
            filtered = categories.get_log_names_for(cat)
            cell.set_property('model', filtered)
            cell.set_property('text', model.get_value(iter, index))


_level_lookup = {"WARNING": "WARN"}
