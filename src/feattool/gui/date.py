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
import gtk


class DateField(object):

    def __init__(self, current=None, input=None, button=None, set_cb=None,
                 format="%b %d %Y %H:%M:%S", parent=None):
        self.current = current or 0
        self.input = input
        self.button = button
        self.set_cb = set_cb
        self.parent = parent
        self.format = format

        self._update_date()
        self.button.connect('clicked', lambda *_: self._pick_date())

    def set_current(self, current):
        self.current = current
        self._update_date()

    def get_current(self):
        return self.current

    def _pick_date(self):
        datepicker = DatePicker(
            title="Pick date",
            parent=self.parent,
            current=self.get_current())
        datepicker.connect('response', self._pick_date_response)
        datepicker.show_all()

    def _pick_date_response(self, dialog, response):
        self.set_current(response)
        if callable(self.set_cb):
            self.set_cb(response)
        dialog.destroy()

    def _update_date(self):
        if self.input is None:
            return
        self.input.set_text(time.strftime(
            self.format,
            time.localtime(float(self.get_current() or 0))))


class DatePicker(gtk.Dialog):

    def __init__(self, title, parent, current):
        gtk.Dialog.__init__(self, title, parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        if current is None:
            current = 0
        self._current = current


        layout = gtk.VBox()
        calendar = gtk.Calendar()
        layout.add(calendar)
        self.vbox.pack_start(layout)

        year, month, mmday, hour, min, sec, daw, yday, isdst = \
              time.localtime(float(current))
        calendar.select_month(month, year)
        calendar.select_day(mmday)
        self.calendar = calendar

        timebox = gtk.HBox()
        timebox.add(gtk.Label(str="Time: "))
        timeinput = gtk.Entry()
        self.timeinput = timeinput
        formated = time.strftime("%H:%M:%S", time.localtime(float(current)))
        timeinput.set_text(formated)
        timebox.add(timeinput)
        layout.add(timebox)

        button = gtk.Button(label="OK")
        layout.add(button)
        button.connect('clicked', self._render_resp)

    def _render_resp(self, button):
        year = self.calendar.get_property('year')
        month = self.calendar.get_property('month')
        day = self.calendar.get_property('day')

        hour, min, sec = map(int, self.timeinput.get_text().split(':'))
        parsed = time.mktime((year, month, day, hour, min, sec, 0, 1, -1))
        self.response(int(parsed))
