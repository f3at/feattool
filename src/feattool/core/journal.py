import pprint
import gobject
import os
import gtk

from zope.interface import classProvides

from feat import everything
from feat.common import log, defer
from feat.agencies import journaler, replay

from feattool.core import component
from feattool.gui import journal

from feattool.interfaces import *


@component.register
class JournalComponent(log.LogProxy, log.Logger):
    classProvides(IGuiComponent)

    def __init__(self, main):
        log.Logger.__init__(self, main)
        log.LogProxy.__init__(self, main)

        self.main = main
        self._journaler = None

        self.je_store = gtk.ListStore(
            str, str, str, str, str, gobject.TYPE_PYOBJECT,
            gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
            gobject.TYPE_PYOBJECT, str)
        self.agents_store = gtk.ListStore(str, bool, int,
                                          gobject.TYPE_PYOBJECT)
        self.details_store = gtk.TreeStore(str, str)

        self.controller = journal.Controller(
            self, self.je_store, self.agents_store, self.details_store)

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
        self._journaler = journaler.Journaler(self, filename=filename)
        d = self._journaler.initiate()
        d.addCallback(lambda _: self._journaler.get_histories())
        d.addCallback(self._got_histories)
        return d

    def show_journal(self, iter):
        '''
        @param iter: TreeIter point to the row in self.agents_store
        to be displayed
        '''
        d = defer.succeed(None)
        if iter:
            history = self.agents_store.get_value(iter, 3)
            d.addCallback(defer.drop_result,
                          self._journaler.get_entries, history)
            d.addCallback(self._parse_history, history.agent_id)
            return d
        else:
            self.je_store.clear()

    def parse_details_for(self, iter):
        '''
        @param iter: TreeIter point to the row in self.je_store to be displayed
        '''
        def append_row(parent, key, value):
            row = self.details_store.append(parent, (key, value, ))
            return row

        def get_value(index):
            return self.je_store.get_value(iter, index)

        def render_list(parent, llist):
            for value, index in zip(llist, range(len(llist))):
                append_row(parent, index, repr(value))

        def render_dict(parent, ddict):
            for key, value in ddict.iteritems():
                append_row(parent, key, repr(value))

        self.details_store.clear()
        append_row(None, 'function_id', get_value(2))

        args = get_value(5)
        if args:
            row = append_row(None, 'arguments', None)
            render_list(row, args)

        kwargs = get_value(6)
        if kwargs:
            row = append_row(None, 'keywords', None)
            render_dict(row, kwargs)

        append_row(None, 'fiber_depth', get_value(4))
        append_row(None, 'result', pprint.pformat(get_value(8)))

        side_effects = get_value(7)
        if side_effects:
            row = append_row(None, 'side_effects', None)
            render_list(row, side_effects)

    ### private ###

    def _got_histories(self, histories):
        self.agents_store.clear()
        for history in histories:
            row = self.agents_store.append()
            self.agents_store.set(row, 0, history.agent_id)
            self.agents_store.set(row, 1, False)
            self.agents_store.set(row, 2, history.instance_id)
            self.agents_store.set(row, 3, history)

    def _parse_history(self, history, agent_id):
        self.je_store.clear()
        self.info('Reading %r entries.', len(history))
        rep = replay.Replay(iter(history), agent_id)
        for entry in rep:
            row = self.je_store.append()
            self.je_store.set(row, 0, entry.agent_id)
            self.je_store.set(row, 1, str(entry.journal_id))
            self.je_store.set(row, 2, entry.function_id)
            self.je_store.set(row, 3, entry.fiber_id)
            self.je_store.set(row, 4, entry.fiber_depth)
            args, kwargs = entry.get_arguments()
            self.je_store.set(row, 5, args)
            self.je_store.set(row, 6, kwargs)
            sfx = map(lambda row: self._parse_sfx(row, entry, rep),
                      entry._side_effects)
            self.je_store.set(row, 7, sfx)
            self.je_store.set(row, 8, entry.result)
            self.je_store.set(row, 9, entry._timestamp)

    def _parse_sfx(self, row, journal_entry, rep):
        sfx = list(journal_entry._restore_side_effect(row))
        sfx[4] = rep.unserializer.convert(sfx[4])
        return sfx












