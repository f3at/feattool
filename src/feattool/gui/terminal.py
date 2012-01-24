#!/usr/bin/env python
#
#      VirtualTerminal.py
#
#      Copyright 2007 Edward Andrew Robinson <earobinson@gmail>
#
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

# Imports
import os
import vte
import gtk
import time

class VirtualTerminal(vte.Terminal):

    def __init__(self, log_file = None, history_length = 5,
                 prompt_watch = {}, prompt_auto_reply = True, icon = None):
        # Set up terminal
        vte.Terminal.__init__(self)

        self._pid = None
        self.history = []
        self.history_length = history_length
        self.icon = icon
        self.last_row_logged = 0
        self.prompt_auto_reply = prompt_auto_reply
        self.prompt_watch = prompt_watch
        self.thread_running = False

        self.connect('eof', self.run_command_done_callback)
        self.connect('child-exited', self.run_command_done_callback)
        self.connect('cursor-moved', self.contents_changed_callback)

    def capture_text(self,text,text2,text3,text4):
        return True

    def contents_changed_callback(self, terminal):
        '''Gets the last line printed to the terminal, it will log
        this line using self.log() (if the logger is on, and it will
        also prompt this line using self.prompt() if the line needs
        prompting'''
        column,row = self.get_cursor_position()
        if self.last_row_logged != row:
            off = row-self.last_row_logged
            text = self.get_text_range(row-off,0,row-1,-1,self.capture_text)
            self.last_row_logged=row
            text = text.strip()

            # Prompter
            self.prompter()

    def get_last_line(self):
        terminal_text = self.get_text(self.capture_text)
        terminal_text = terminal_text.split('\\\\n')
        ii = len(terminal_text) - 1
        while terminal_text[ii] == '':
            ii = ii - 1
        terminal_text = terminal_text[ii]

        return terminal_text

    def prompter(self):
        last_line = self.get_last_line()
        if last_line in self.prompt_watch:
            if self.prompt_auto_reply == False:
                message = ''
                for ii in self.prompt_watch[last_line]:
                    message = message + self.history[self.history_length - 1 - ii]
                if self.yes_no_question(message):
                    self.feed_child('Yes\\\\n')
                    # TODO not sure why this is needed twice
                    self.feed_child('Yes\\\\n')
                else:
                    self.feed_child('No\\\\n')
            else:
                self.feed_child('Yes\\\\n')

    def run_command(self, command_string):
        '''run_command runs the command_string in the terminal. This
        function will only return when self.thred_running is set to
        True, this is done by run_command_done_callback'''
        if self.thread_running:
            raise ValueError("Already running")
        self.thread_running = True
        spaces = ''
        for ii in range(80 - len(command_string) - 2):
            spaces = spaces + ' '
        self.feed('$ ' + str(command_string) + spaces)

        command = command_string.split(' ')
        self._pid = self.fork_command(
            command=command[0], argv=command, directory=os.getcwd())

    def run_command_done_callback(self, terminal):
        '''When called this function sets the thread as done allowing
        the run_command function to exit'''
        self.thread_running = False
        self._pid = None
