#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys
from threading import currentThread
from Tkinter import (Tk, Toplevel, Frame, Listbox, Label, Button, Entry,
                     BOTH, END, LEFT, W)


class _AbstractTkDialog(Toplevel):
    _left_button = 'OK'
    _right_button = 'Cancel'

    def __init__(self, message, *args):
        self._prevent_execution_with_timeouts()
        Toplevel.__init__(self, self._get_parent())
        self._init_dialog()
        self._create_body(message, args)
        self._create_buttons()
        self.wait_window(self)

    def _prevent_execution_with_timeouts(self):
        if 'linux' not in sys.platform \
                and currentThread().getName() != 'MainThread':
            raise RuntimeError('Dialogs library is not supported with '
                               'timeouts on Python on this platform.')

    def _get_parent(self):
        parent = Tk()
        parent.withdraw()
        return parent

    def _init_dialog(self):
        self.title('Robot Framework')
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._right_button_clicked)
        self.bind("<Escape>", self._right_button_clicked)
        self.minsize(250, 80)
        self.geometry("+%d+%d" % self._get_center_location())
        self._bring_to_front()

    def _get_center_location(self):
        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) / 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) / 2
        return x, y

    def _bring_to_front(self):
        self.attributes('-topmost', True)
        self.attributes('-topmost', False)

    def _create_body(self, message, args):
        frame = Frame(self)
        Label(frame, text=message, anchor=W, justify=LEFT).pack(fill=BOTH)
        selector = self._create_selector(frame, *args)
        if selector:
            selector.pack(fill=BOTH)
            selector.focus_set()
        frame.pack(padx=5, pady=5, expand=1, fill=BOTH)

    def _create_selector(self, frame):
        return None

    def _create_buttons(self):
        frame = Frame(self)
        self._create_button(frame, self._left_button,
                            self._left_button_clicked)
        self._create_button(frame, self._right_button,
                            self._right_button_clicked)
        frame.pack()

    def _create_button(self, parent, label, callback):
        if label:
            button = Button(parent, text=label, width=10, command=callback)
            button.pack(side=LEFT, padx=5, pady=5)

    def _left_button_clicked(self, event=None):
        if self._validate_value():
            self.result = self._get_value()
            self.destroy()

    def _get_value(self):
        return None

    def _validate_value(self):
        return True

    def _right_button_clicked(self, event=None):
        self.result = self._get_right_button_value()
        self.destroy()

    def _get_right_button_value(self):
        return None


class MessageDialog(_AbstractTkDialog):
    _right_button = None


class InputDialog(_AbstractTkDialog):

    def __init__(self, message, default=''):
        _AbstractTkDialog.__init__(self, message, default)

    def _create_selector(self, parent, default):
        self._entry = Entry(parent)
        self._entry.insert(0, default)
        self._entry.select_range(0, END)
        return self._entry

    def _get_value(self):
        return self._entry.get()


class SelectionDialog(_AbstractTkDialog):

    def __init__(self, message, values):
        _AbstractTkDialog.__init__(self, message, values)

    def _create_selector(self, parent, values):
        self._listbox = Listbox(parent)
        for item in values:
            self._listbox.insert(END, item)
        return self._listbox

    def _validate_value(self):
        return bool(self._listbox.curselection())

    def _get_value(self):
        return self._listbox.get(self._listbox.curselection())


class PassFailDialog(_AbstractTkDialog):
    _left_button = 'PASS'
    _right_button = 'FAIL'

    def _get_value(self):
        return True

    def _get_right_button_value(self):
        return False
