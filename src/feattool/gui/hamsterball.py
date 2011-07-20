import pango
import types
import gobject
import gtk
import pydot

from feattool.extern import xdot
from feat.common import first


class Model(gtk.ListStore):

    __gsignals__ = {"graph-changed": (gobject.SIGNAL_RUN_LAST,
                                      gobject.TYPE_NONE,
                                      [gobject.TYPE_PYOBJECT])}

    def __init__(self):
        # journal_id, Replayable
        gtk.ListStore.__init__(
            self, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
        self._details = gtk.TreeStore(str, gobject.TYPE_PYOBJECT)

    def clear(self):
        gtk.ListStore.clear(self)
        self._render()

    def append(self, values):
        res = gtk.ListStore.append(self, values)
        self._render()
        return res

    def append_iter(self, iter):
        for values in iter:
            gtk.ListStore.append(self, values)
        self._render()

    def get_details_model(self):
        return self._details

    ### private ###

    def _render(self, *_):
        self._details.clear()

        state = RenderState()

        for row in self:
            journal_id, replayable = row
            self._render_replayable(replayable, state)
            state.append_inside_hamsterball(replayable)

        graph = state.finalize()
        self.emit('graph-changed', graph)

    def _render_replayable(self, replayable, render_state):
        journal_id = replayable.journal_id

        row = self._append_row(None, journal_id, None)
        mutable_state = replayable._get_state()
        visited = set()
        self._render_structure(row, mutable_state.__dict__.iteritems(),
                               visited, journal_id, render_state)

    def _render_structure(self, parent_row, iterator, visited, owner_url,
                          render_state):
        index = 0
        for element in iterator:
            if isinstance(element, tuple) and len(element) == 2:
                key, value = element
            else:
                key = index
                value = element
            index += 1

            if str(key)[0] == '_':
                # respect the privacy of classes ;)
                continue
            if id(element) in visited:
                self._append_row(parent_row, key, "Cyclic reference")
                continue
            basic_types = (int, str, unicode, float, type, bool,
                           types.NoneType)
            if isinstance(value, basic_types):
                self._append_row(parent_row, key, value)
                continue
            if self._includes_value(value):
                ref = render_state.add_reference(
                    type(value).__name__, owner_url, value.journal_id)
                self._append_row(parent_row, key, ref)
                continue
            if hasattr(value, '_outside_hamsterball_tag'):
                ref = render_state.add_reference(
                    type(value).__name__, owner_url, id(value))
                self._append_row(parent_row, key, ref)
                render_state.append_outside_hamsterball(value)
                continue

            iterable_types = (dict, list, tuple, set, )
            if isinstance(value, iterable_types):
                row = self._append_row(parent_row, key, type(value).__name__)
                if hasattr(value, 'iteritems'):
                    new_iterator = value.iteritems()
                else:
                    new_iterator = iter(value)
                visited.add(id(value))
                self._render_structure(row, new_iterator, visited, owner_url,
                                       render_state)
                continue

            new_iter = value.__dict__.iteritems()
            row = self._append_row(parent_row, key, type(value).__name__)
            visited.add(id(value))
            self._render_structure(row, new_iter, visited, owner_url,
                                   render_state)

    def _includes_value(self, value):
        for row in self:
            if value == row[1]:
                return True
        return False

    def _append_row(self, parent, key, value):
        row = self._details.append(parent, (key, value, ))
        return row


class Reference(object):

    def __init__(self, name, owner_url, url):
        self.name = name
        self.url = url
        self.owner_url = owner_url

    def __repr__(self):
        return "Ref: %s %r" % (self.name, self.url, )


class HamsterballWidget(gtk.HPaned):

    def __init__(self, model=None):
        gtk.HPaned.__init__(self)

        self._selected = None
        self._graph = None

        self._xdot = DotWidget()

        self.add(self._xdot)
        self._xdot.show_all()
        self._xdot.connect('clicked', self._xdot_clicked)

        self._details = Details()
        self._details.show_all()
        self._details.connect('highlight-reference',
                              self._select_reference_handler)
        self.add(self._details)
        self.set_property('position', 550)

        self.set_model(model)

    def set_model(self, model):
        self._model = model
        if self._model is not None:
            self._update_details()
            model.connect('graph-changed', self._update_xdot)

    def get_model(self):
        return self._model

    def select(self, url):
        self._selected = url
        self._highlight_selected()
        self._update_details()

    ### private ###

    def _select_reference_handler(self, model, reference):
        if reference is None:
            self._highlight_selected()
            return
        src = self._get_node(str(reference.owner_url))
        dst = self._get_node(str(reference.url))
        edge = first(x for x in self._xdot.graph.edges
                     if x.src == src and x.dst == dst)
        if edge:
            self._xdot.set_highlight([src, edge])

    def _highlight_selected(self):
        url = self._get_selected()
        if url is None:
            self._xdot.set_highlight([])
        node = self._get_node(url)
        if node:
            self._xdot.set_highlight([node])

    def _get_node(self, url):
        if self._graph is None:
            return
        node = first(x for x in self._xdot.graph.nodes
                     if x.url == url)
        return node

    def _update_details(self):
        self._details.set_model(None)

        model = self.get_model()
        if model is None:
            return
        model = model.get_details_model()
        selected = self._get_selected()
        if selected:
            row = self._find_root(model, selected)
            if row is None:
                return
            filtered = model.filter_new(model.get_path(row.iter))
            self._details.set_model(filtered)

    def _find_root(self, model, selected):
        for row in model:
            if row[0] == selected:
                return row

    def _get_selected(self):
        return self._selected

    def _xdot_clicked(self, widget, url, event):
        self.select(url)

    def _update_xdot(self, model, graph):
        rect = self._xdot.get_allocation()
        graph.obj_dict['attributes']['ratio'] = float(rect.height)/rect.width
        self._graph = graph
        dotcode = graph.to_string()
        self._xdot.set_dotcode(dotcode)
        if self._xdot.graph.width:
            self._xdot.zoom_to_fit()


class Details(gtk.TreeView):

    __gsignals__ = {"highlight-reference": (gobject.SIGNAL_RUN_LAST,
                                            gobject.TYPE_NONE,
                                            [gobject.TYPE_PYOBJECT])}

    def __init__(self, model=None):
        gtk.TreeView.__init__(self, model)

        renderer = gtk.CellRendererText()
        columns = ("Field", "Value")
        for column, index in zip(columns, range(len(columns))):
            col = gtk.TreeViewColumn(column)
            col.set_resizable(True)
            col.set_min_width(80)
            col.pack_start(renderer, True)
            col.set_cell_data_func(renderer, self._render_details, index)
            self.append_column(col)

        self.connect('cursor_changed', self._detail_cursor_changed)

    def _render_details(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('text', str(value))
        cell.set_property('editable', True)
        cell.set_property('wrap-mode', pango.WRAP_WORD)

    def _detail_cursor_changed(self, treeview):
        path, focus = treeview.get_cursor()
        model = self.get_model()
        iter = model.get_iter(path)
        value = model.get_value(iter, 1)

        if not isinstance(value, Reference):
            value = None
        self.emit('highlight-reference', value)


class RenderState(object):
    '''
    I hold temporary data necessary to render the hamsterball graph.
    '''

    def __init__(self):
        self._graph = pydot.Dot(
            graph_type='digraph')
        self._hamsterball = pydot.Subgraph(
            graph_name='hamsterball',
            color='lightyellow',
            style='filled')

        self._graph.add_subgraph(self._hamsterball)

        self._references = dict()

    def append_inside_hamsterball(self, replayable):
        journal_id = replayable.journal_id
        node = pydot.Node(
            name=str(journal_id),
            label=type(replayable).__name__,
            style="filled",
            color="lightblue",
            URL=str(journal_id))
        self._hamsterball.add_node(node)

    def append_outside_hamsterball(self, instance):
        node = pydot.Node(
            name=str(id(instance)),
            label=type(instance).__name__,
            URL=str(id(instance)))
        self._graph.add_node(node)

    def finalize(self):
        self._add_edges()
        return self.get_graph()

    def add_reference(self, name, src, dst):
        key = (str(src), str(dst))
        ref = self._references.get(key, None)
        if ref is None:
            ref = Reference(name, src, dst)
        self._references[key] = ref
        return ref

    def get_graph(self):
        return self._graph

    def _add_edges(self):
        for (src, dst), ref in self._references.iteritems():
            if src == dst:
                # don't display self references
                continue
            edge = pydot.Edge(src=src, dst=dst)
            self._graph.add_edge(edge)


class NoAction(xdot.DragAction):

    def on_motion_notify(self, event):
        # original handler changes highlight of elements on hover,
        # we don't want this behaviour
        pass


class DotWidget(xdot.DotWidget):

    null_action = NoAction
