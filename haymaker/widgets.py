#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Wrappers and utils for common PyQt classes/functions.
"""


# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------- IMPORTS --#

# Built-In
import os.path

# Third Party
from PySide2 import QtWidgets, QtCore, QtGui

# Internal
from haymaker.enums import ResultType, WindowMode
from haymaker.log import log, Level

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def set_parent(parent, child, child_super, **kwargs):
    if isinstance(parent, QtWidgets.QLayout):
        child_super.__init__(**kwargs)
        if isinstance(child, QtWidgets.QWidget):
            parent.addWidget(child)
        elif isinstance(child, QtWidgets.QLayout):
            parent.addLayout(child)
        else:
            raise RuntimeError()
    else:
        child_super.__init__(parent, **kwargs)


def get_resource_path(name, resolution='full'):
    return os.path.join(os.path.dirname(__file__), 'resources', resolution, name)


def get_app():
    return QtWidgets.QApplication()


def run_app(app):
    import sys
    sys.exit(app.exec_())


#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#


#region Dialogs
class Dialog(QtWidgets.QDialog):
    icon_name = ('so_much_win.png', '032')
    default_title = "Wrapped Dialog"
    default_size = (900, 750)
    default_position = None
    size_is_fixed = False
    closeable = True
    window_mode = WindowMode.Show

    def __init__(self, parent=None, init=True, **kwargs):
        super().__init__(parent)
        if init:
            self.init(**kwargs)

    def init(self, **kwargs):
        # set size
        if self.size_is_fixed:
            self.setFixedSize(self.default_size[0], self.default_size[1])
        else:
            self.resize(self.default_size[0], self.default_size[1])

        # set position
        if self.default_position:
            self.move(self.default_position[0], self.default_position[1])

        # set title and icon
        self.setWindowTitle(self.default_title)
        if self.icon_name:
            icon_path = get_resource_path(*self.icon_name)
            if os.path.isfile(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
            else:
                log(f'Unable to find icon at {icon_path}', Level.ERROR)

        # config the help and close button
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, self.closeable)

        # show the dialog
        if self.window_mode == WindowMode.Show:
            self.show()
        elif self.window_mode == WindowMode.Modal:
            self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            self.show()
        elif self.window_mode == WindowMode.Exec:
            self.exec_()
        else:
            log(f'unknown window mode {self.window_mode}', Level.ERROR)


class NotifyUser(Dialog):
    default_position = None
    window_mode = WindowMode.Exec

    def __init__(self, title, message, size=(200, 240), notify_type=ResultType.SUCCESS):
        self.default_title = title
        self.default_size = size

        super().__init__(message=message, notify_type=notify_type)

    def init(self, message, notify_type=ResultType.SUCCESS):
        vb_main = VLayout(self)

        # get status icon
        if not notify_type or notify_type == ResultType.FAILURE:
            img_name = 'cancel_icon.png'
        elif notify_type == ResultType.WARNING:
            img_name = 'warning_icon.png'
        else:
            img_name = 'accept_icon.png'

        # show status icon
        icon_status = Label(
            img_name, resolution='150', parent=vb_main,
            stylesheet='border: 1px solid black'
        )
        icon_status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # show message
        lbl_message = Label(message, vb_main)
        lbl_message.setWordWrap(True)
        lbl_message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # show exit button
        Button(
            'Ok', self.close, vb_main,
            stylesheet='background-color: green; color: white;'
        )

        super().init()


class UserConfirm(Dialog):
    default_position = None
    window_mode = WindowMode.Exec
    closeable = False

    def __init__(self, title, message, confirm='yes', cancel='no', size=(250, 100)):
        self.default_title = title
        self.default_size = size
        super().__init__(message=message, confirm=confirm, cancel=cancel)

    def init(self, message, confirm, cancel):
        # Make a layout.
        vb_main = VLayout(self)

        # Add the text field.
        lbl = Label(message, vb_main)
        lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)

        # Add the two buttons.
        hb_buttons = HLayout(vb_main)
        btn_confirm = Button(confirm, self.confirm_clicked, hb_buttons,
                             stylesheet='background-color: oliveDrab; color: white;')
        btn_cancel = Button(cancel, self.cancel_clicked, hb_buttons,
                            stylesheet='background-color: crimson; color: white;')

        # Add the layouts together and show the result.
        super().init()

    def confirm_clicked(self):
        """
        This method handles what happens when the user clicks the confirm button.

        :return: A yes response.
        :type: QtGui.QMessageBox.Yes
        """
        # Close the window and send a yes signal.
        self.result = True
        self.close()

    def cancel_clicked(self):
        """
        This method handles what happens when the user clicks the cancel button.

        :return: A yes response.
        :type: QtGui.QMessageBox.Yes
        """
        # Close the window and send a yes signal.
        self.result = False
        self.close()
#endregion


#region Layouts
class VLayout(QtWidgets.QVBoxLayout):
    def __init__(self, parent=None):
        set_parent(parent, self, super())


class HLayout(QtWidgets.QHBoxLayout):
    def __init__(self, parent=None):
        set_parent(parent, self, super())


class FormLayout(QtWidgets.QFormLayout):
    def __init__(self, parent=None):
        set_parent(parent, self, super())

    def add_readonly_row(self, label: str, value: str):
        le_value = QtWidgets.QLineEdit()
        le_value.setText(value)
        le_value.setReadOnly(True)
        le_value.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.addRow(label, le_value)
        return le_value


class GridLayout(QtWidgets.QGridLayout):
    def __init__(self, parent=None):
        set_parent(parent, self, super())
#endregion


#region Widgets
class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        set_parent(parent, self, super())


class Button(QtWidgets.QPushButton):
    def __init__(self, text: str, callback, parent=None, stylesheet=None):
        """
        Creates a button with the provided label that performs the callback on click.
        """
        set_parent(parent, self, super(), text=text)
        self.clicked.connect(callback)
        if stylesheet:
            self.setStyleSheet(stylesheet)


class Label(QtWidgets.QLabel):
    def __init__(self, text, parent=None, stylesheet=None, resolution=None, is_path=None,
                 width=None):
        self.pixel_map = None
        self.resolution = resolution
        self.is_path = is_path
        if not resolution and not is_path:
            set_parent(parent, self, super(), text=text)
        else:
            set_parent(parent, self, super())
            self.set_image(text, width=width)
        if stylesheet:
            self.setStyleSheet(stylesheet)

    def set_image(self, name, resolution=None, is_path=None, width=None):
        if is_path:
            self.is_path = is_path
        if resolution:
            self.resolution = resolution

        path_img = name
        if not self.is_path:
            path_img = get_resource_path(name, self.resolution)

        if not os.path.isfile(path_img):
            log(f'could not find image at {path_img}', Level.ERROR)
            self.pixel_map = None
            self.setPixmap(self.pixel_map)
            return None

        self.pixel_map = QtGui.QPixmap(path_img)
        if width:
            self.pixel_map = self.pixel_map.scaledToWidth(width)
        self.setPixmap(self.pixel_map)
        return True


class ComboBox(QtWidgets.QComboBox):
    def __init__(self, values, parent=None):
        set_parent(parent, self, super())
        self.addItems(values)
#endregion


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


def main():
    import sys
    app = QtWidgets.QApplication()
    notify = UserConfirm('Example Notify', 'LISTEN TO ME!')
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
