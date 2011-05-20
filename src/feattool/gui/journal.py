import gtksourceview2
import gobject
import gtk

from feat.common import log

from feattool import data


class Controller(log.Logger, log.LogProxy):
    """
    This is the controller of journal viewer component.
    """

    def __init__(self, model, journal_entries, agent_list,
                 entry_details, code_preview):
        log.Logger.__init__(self, model)
        log.LogProxy.__init__(self, model)

        self.model = model

        self.builder = gtk.Builder()
        self.builder.add_from_file(data.path('ui', 'main.ui'))
        self.builder.add_from_file(data.path('ui', 'journal-viewer.ui'))

        self.view = MainWindow(self, self.builder,
                               journal_entries, agent_list,
                               entry_details, code_preview)
        self.view.show()

    def quit(self):
        self.model.finished()

    ### called by view ###

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

    def show_journal(self, iter):
        self.model.show_journal(iter)

    def show_entry_details(self, iter):
        self.model.parse_details_for(iter)

    ### called by model ###

    def display_error(self, msg):
        dialog = gtk.Dialog("Error", self.view.window,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, ))
        label = gtk.Label(msg)
        label.set_padding(20, 20)
        dialog.vbox.pack_start(label)
        dialog.show_all()
        dialog.connect('response', lambda *_: dialog.destroy())

    ### private ###

    def _choose_jourfile_response(self, dialog, response_id):
        selected = dialog.get_filenames()
        dialog.destroy()
        if response_id == gtk.RESPONSE_OK:
            self.model.load_jourfile(selected[0])


class MainWindow(log.Logger):
    """
    This is the view of main journal viewer window.
    """

    def __init__(self, controller, builder, journal_entries_store,
                 agents_store, entry_details, code_preview):
        log.Logger.__init__(self, controller)

        self.controller = controller
        self.builder = builder

        self.journal_entries_store = journal_entries_store
        self.agents_store = agents_store
        self.entry_details = entry_details
        self.code_preview = code_preview

        self._setup_window()
        self._setup_menu()
        self._setup_lists()
        self._setup_buttons()

    def _setup_window(self):
        self.window = self.builder.get_object('journal_viewer')
        self.window.set_title('Journal viewer')
        self.window.connect('destroy', self._on_destroy)
        self.window.resize(800, 600)

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

    def _setup_buttons(self):
        clear = self.builder.get_object('clear_search')
        search = self.builder.get_object('je_search')
        clear.connect('clicked', lambda *_: search.set_text(''))

    def _setup_source_preview(self):
        code_view = gtksourceview2.View(self.code_preview)
        code_view.show_all()
        self.builder.get_object('code_preview').add(code_view)

    def _setup_agent_list(self):
        agent_list = AgentList(model=self.agents_store)
        agent_list.show_all()
        self.builder.get_object('agents_list').add(agent_list)

        agent_list.connect('agent-marked',
                           lambda _, iter: self.controller.show_journal(iter))

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

    def _setup_columns(self):
        renderer = gtk.CellRendererText()
        toggle_renderer = gtk.CellRendererToggle()
        toggle_renderer.connect('toggled', self._agent_toggle_toggled)
        col = gtk.TreeViewColumn('')
        col.pack_start(toggle_renderer, False)
        col.add_attribute(toggle_renderer, 'active', 1)
        self.append_column(col)

        col = gtk.TreeViewColumn('Agent ID')
        col.pack_start(renderer, True)
        col.set_cell_data_func(renderer, self._render_agent_entry, 0)
        self.append_column(col)

        col = gtk.TreeViewColumn('Instance ID')
        col.pack_start(renderer, True)
        col.set_cell_data_func(renderer, self._render_agent_entry, 2)
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


class JournalEntries(gtk.TreeView):

    __gsignals__ = {"entry-marked": (gobject.SIGNAL_RUN_LAST,\
                                     gobject.TYPE_NONE, [gtk.TreeIter])}

    def __init__(self, model=None, search=None):
        model_f = model.filter_new()
        model_f.set_visible_func(self._je_visible)

        gtk.TreeView.__init__(self, model_f)
        self._selected_fiber_id = None

        self._search = search
        self._search.connect('changed', lambda *_: model_f.refilter())

        self._setup_columns()
        self.connect('cursor_changed', self._journal_cursor_changed)

    def _setup_columns(self):
        text_renderer = gtk.CellRendererText()
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
        self.queue_draw()

    def _render_journal_entry(self, column, cell, model, iter):
        value = model.get_value(iter, 2)
        cell.set_property('text', value)

        cell.set_property('weight-set', True)
        fiber_id = model.get_value(iter, 3)
        if self._selected_fiber_id and self._selected_fiber_id == fiber_id:
            weight = 700
        else:
            weight = 400

        cell.set_property('weight', weight)

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
            col.pack_start(renderer, True)
            col.set_cell_data_func(renderer, self._render_details, index)
            self.append_column(col)

    def _render_details(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('text', value)
