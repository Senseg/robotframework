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

import time
from javax.swing import JOptionPane
from javax.swing.JOptionPane import PLAIN_MESSAGE, UNINITIALIZED_VALUE, \
    YES_NO_OPTION, OK_CANCEL_OPTION, DEFAULT_OPTION


class _AbstractSwingDialog:

    def __init__(self, pane):
        self._show_dialog(pane)
        self.result = self._get_value(pane)

    def _show_dialog(self, pane):
        dialog = pane.createDialog(None, 'Robot Framework')
        dialog.setModal(False)
        dialog.setAlwaysOnTop(True)
        dialog.show()
        while dialog.isShowing():
            time.sleep(0.2)
        dialog.dispose()

    def _get_value(self, pane):
        value = pane.getInputValue()
        return value if value != UNINITIALIZED_VALUE else None


class MessageDialog(_AbstractSwingDialog):

    def __init__(self, message):
        pane = JOptionPane(message, PLAIN_MESSAGE, DEFAULT_OPTION)
        _AbstractSwingDialog.__init__(self, pane)


class InputDialog(_AbstractSwingDialog):

    def __init__(self, message, default):
        pane = JOptionPane(message, PLAIN_MESSAGE, OK_CANCEL_OPTION)
        pane.setWantsInput(True)
        pane.setInitialSelectionValue(default)
        _AbstractSwingDialog.__init__(self, pane)


class SelectionDialog(_AbstractSwingDialog):

    def __init__(self, message, options):
        pane = JOptionPane(message, PLAIN_MESSAGE, OK_CANCEL_OPTION)
        pane.setWantsInput(True)
        pane.setSelectionValues(options)
        _AbstractSwingDialog.__init__(self, pane)


class PassFailDialog(_AbstractSwingDialog):

    def __init__(self, message):
        pane = JOptionPane(message, PLAIN_MESSAGE, YES_NO_OPTION,
                           None, ['PASS', 'FAIL'], 'PASS')
        _AbstractSwingDialog.__init__(self, pane)

    def _get_value(self, pane):
        return pane.getValue() == 'PASS'
