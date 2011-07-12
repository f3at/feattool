import time
import gtk
import pango


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
        timeinput  = gtk.Entry()
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
