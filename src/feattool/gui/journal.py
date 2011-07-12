import time
import pango
import gtksourceview2
import gobject
import gtk

from feat.common import log, first

from feattool import data
from feattool.gui import hamsterball, date
from feattool.core import settings


class Controller(log.Logger, log.LogProxy):
    """
    This is the controller of journal viewer component.
    """

    def __init__(self, model, journal_entries, agent_list,
                 entry_details, code_preview, hamsterball):
        log.Logger.__init__(self, model)
        log.LogProxy.__init__(self, model)

        self.model = model

        self.builder = gtk.Builder()
        self.builder.add_from_file(data.path('ui', 'main.ui'))
        self.builder.add_from_file(data.path('ui', 'journal-viewer.ui'))

        self.view = MainWindow(self, self.builder,
                               journal_entries, agent_list,
                               entry_details, code_preview, hamsterball)
        self.view.show()

        self._start_date = None
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
        self._start_date = epoc
        obj = self.builder.get_object('start_date')
        timestamp = time.strftime("%b %d %Y %H:%M:%S",
                                  time.localtime(float(self._start_date)))
        obj.set_text(timestamp)
        self.show_journal()

    def get_start_date(self):
        return self._start_date or 0

    def set_end_date(self, epoc):
        self._end_date = epoc
        obj = self.builder.get_object('end_date')
        timestamp = time.strftime("%b %d %Y %H:%M:%S",
                                  time.localtime(float(self._end_date)))
        obj.set_text(timestamp)
    ### called by view ###

    def pick_date(self):
        datepicker = date.DatePicker(
            title="Pick start date",
            parent=self.view.window,
            current = self._start_date)
        datepicker.connect('response', self._pick_date_response)
        datepicker.show_all()

    def choose_jourfile(self):
        filechooser = gtk.FileChooserDialog(
            title='Choose journal file',
            parent=self.view.window,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filechooser.connect('response', self._choose_jourfile_response)
        filechooser.show_all()

    def open_imports_manager(self):
        self.model.main.show_imports_manager()

    def show_journal(self):
        iter = self.view.agent_list.get_marked_iter()
        self.model.show_journal(iter)

    def show_entry_details(self, iter):
        self.model.parse_details_for(iter)

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

    def _pick_date_response(self, dialog, response):
        self.set_start_date(response)
        dialog.destroy()


class MainWindow(log.Logger):
    """
    This is the view of main journal viewer window.
    """

    def __init__(self, controller, builder, journal_entries_store,
                 agents_store, entry_details, code_preview, hamsterball):
        log.Logger.__init__(self, controller)

        self.controller = controller
        self.builder = builder

        self.journal_entries_store = journal_entries_store
        self.agents_store = agents_store
        self.entry_details = entry_details
        self.code_preview = code_preview
        self.hamsterball = hamsterball

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

        action = self.builder.get_object('quit_menuitem')
        action.connect('activate', self._on_destroy)

        menu = self.builder.get_object('imports_menuitem')
        menu.connect('activate',
                     lambda _: self.controller.open_imports_manager())

    def _setup_lists(self):
        self._setup_agent_list()
        self._setup_journal_entries()
        self._setup_entry_details()
        self._setup_source_preview()
        self._setup_hamsterball()

    def _setup_buttons(self):
        clear = self.builder.get_object('clear_search')
        search = self.builder.get_object('je_search')
        clear.connect('clicked', lambda *_: search.set_text(''))
        but = self.builder.get_object('set_start_end')
        but.connect('clicked', lambda *_: self.controller.set_start_end())

        but = self.builder.get_object('pick_date')
        but.connect('clicked', lambda *_: self.controller.pick_date())

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

    def _journal_entry_marked(self, model, iter):
        self.controller.show_entry_details(iter)
        self.entry_details.expand_all()

    def _on_destroy(self, window):
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
        self._marked = None

    def _setup_columns(self):
        renderer = gtk.CellRendererText()
        toggle_renderer = gtk.CellRendererToggle()
        toggle_renderer.connect('toggled', self._agent_toggle_toggled)
        col = gtk.TreeViewColumn('')
        col.set_min_width(20)
        col.pack_start(toggle_renderer, False)
        col.add_attribute(toggle_renderer, 'active', 1)
        self.append_column(col)

        col = gtk.TreeViewColumn('Agent ID')
        col.pack_start(renderer, True)
        col.set_cell_data_func(renderer, self._render_agent_entry, 0)
        self.append_column(col)

        col = gtk.TreeViewColumn('I ID')
        col.pack_start(renderer, True)
        col.set_cell_data_func(renderer, self._render_agent_entry, 2)
        self.append_column(col)

        col = gtk.TreeViewColumn('Type')
        col.pack_start(renderer, True)
        col.set_cell_data_func(renderer, self._render_agent_entry, 4)
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
        self._marked = param
        self.emit('agent-marked', param)

    def get_marked_iter(self):
        return self._marked

    def _render_agent_entry(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('text', value)


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

        fiber_id = model.get_value(iter, 3)
        if self._selected_fiber_id and self._selected_fiber_id == fiber_id:
            weight = 700
        else:
            weight = 400
        cell.set_property('weight', weight)
        enabled = model.get_value(iter, 11)
        if not enabled:
            color = gtk.gdk.Color(40000, 40000, 40000)
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
        year, month, mmday, hour, min, sec, daw, yday, isdst = \
              time.localtime(float(value))
        formatted = "%s:%s:%s" % (hour, min, sec)
        cell.set_property('text', formatted)

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
        cell.set_property('wrap-width', column.get_property('width'))
        cell.set_property('wrap-mode', pango.WRAP_WORD)