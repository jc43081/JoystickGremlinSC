# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PyQt5 import QtCore, QtGui, QtWidgets

from gremlin import config, profile, util
from gremlin.event_handler import EventListener, InputType
import gremlin.ui_widgets as widgets

from ui_about import Ui_About



class OptionsUi(QtWidgets.QWidget):

    """UI allowing the configuration of a variety of options."""

    # Signal emitted when the dialog is being closed
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Creates a new options UI instance.

        :param parent the parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        # Actual configuration object being managed
        self.config = config.Configuration()

        self.setWindowTitle("Options")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.tab_container = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tab_container)

        self._create_general_page()
        self._create_profile_page()

    def _create_general_page(self):
        self.general_page = QtWidgets.QWidget()
        self.general_layout = QtWidgets.QVBoxLayout(self.general_page)

        # Highlight input option
        self.highlight_input = QtWidgets.QCheckBox(
            "Highlight currently used input"
        )
        self.highlight_input.clicked.connect(self._highlight_input)
        self.highlight_input.setChecked(self.config.highlight_input)

        # Close to system tray option
        self.close_to_systray = QtWidgets.QCheckBox(
            "Closing minimizes to system tray"
        )
        self.close_to_systray.clicked.connect(self._close_to_systray)
        self.close_to_systray.setChecked(self.config.close_to_tray)

        # Show message on mode change
        self.show_mode_change_message = QtWidgets.QCheckBox(
            "Show message when changing mode"
        )
        self.show_mode_change_message.clicked.connect(
            self._show_mode_change_message
        )
        self.show_mode_change_message.setChecked(
            self.config.mode_change_message
        )

        self.general_layout.addWidget(self.highlight_input)
        self.general_layout.addWidget(self.close_to_systray)
        self.general_layout.addWidget(self.show_mode_change_message)
        self.general_layout.addStretch()
        self.tab_container.addTab(self.general_page, "General")

    def _create_profile_page(self):
        self.profile_page = QtWidgets.QWidget()
        self.profile_page_layout = QtWidgets.QVBoxLayout(self.profile_page)

        # Autload profile option
        self.autoload_checkbox = QtWidgets.QCheckBox(
            "Automatically load profile based on current application"
        )
        self.autoload_checkbox.clicked.connect(self._autoload_profiles)
        self.autoload_checkbox.setChecked(self.config.autoload_profiles)

        # Executable dropdown list
        self.executable_layout = QtWidgets.QHBoxLayout()
        self.executable_label = QtWidgets.QLabel("Executable")
        self.executable_selection = QtWidgets.QComboBox()
        self.executable_selection.currentTextChanged.connect(
            self._show_executable
        )
        self.executable_add = QtWidgets.QPushButton()
        self.executable_add.setIcon(QtGui.QIcon("gfx/button_add.png"))
        self.executable_add.clicked.connect(self._new_executable)
        self.executable_remove = QtWidgets.QPushButton()
        self.executable_remove.setIcon(QtGui.QIcon("gfx/button_delete.png"))
        self.executable_remove.clicked.connect(self._remove_executable)

        self.executable_layout.addWidget(self.executable_label)
        self.executable_layout.addWidget(self.executable_selection)
        self.executable_layout.addWidget(self.executable_add)
        self.executable_layout.addWidget(self.executable_remove)
        self.executable_layout.addStretch()

        self.profile_layout = QtWidgets.QHBoxLayout()
        self.profile_field = QtWidgets.QLineEdit()
        self.profile_field.textChanged.connect(self._update_profile)
        self.profile_field.editingFinished.connect(self._update_profile)
        self.profile_select = QtWidgets.QPushButton()
        self.profile_select.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.profile_select.clicked.connect(self._select_profile)

        self.profile_layout.addWidget(self.profile_field)
        self.profile_layout.addWidget(self.profile_select)

        self.profile_page_layout.addWidget(self.autoload_checkbox)
        self.profile_page_layout.addLayout(self.executable_layout)
        self.profile_page_layout.addLayout(self.profile_layout)
        self.profile_page_layout.addStretch()

        self.tab_container.addTab(self.profile_page, "Profiles")

        self.populate_executables()

    def closeEvent(self, event):
        """Closes the calibration window.

        :param event the close event
        """
        self.config.save()
        self.closed.emit()

    def populate_executables(self):
        """Populates the profile drop down menu."""
        self.profile_field.textChanged.disconnect(self._update_profile)
        self.executable_selection.clear()
        for path in self.config.get_executable_list():
            self.executable_selection.addItem(path)
        self.profile_field.textChanged.connect(self._update_profile)

    def _autoload_profiles(self, clicked):
        """Stores profile autoloading preference.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.autoload_profiles = clicked
        self.config.save()

    def _close_to_systray(self, clicked):
        """Stores closing to system tray preference.

        :param clicked whether or not the checkbox is ticked"""
        self.config.close_to_tray = clicked
        self.config.save()

    def _highlight_input(self, clicked):
        """Stores preference for input highlighting.

        :param clicked whether or not the checkbox is ticked"""
        self.config.highlight_input = clicked
        self.config.save()

    def _new_executable(self):
        """Prompts the user to select a new executable to add to the
        profile.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to executable",
            "C:\\",
            "Executable (*.exe)"
        )
        if fname != "":
            self.config.set_profile(fname, "")
            self.populate_executables()
            self._show_executable(fname)

    def _remove_executable(self):
        """Removes the current executable from the configuration."""
        self.config.remove_profile(self.executable_selection.currentText())
        self.populate_executables()

    def _select_profile(self):
        """Displays a file selection dialog for a profile.

        If a valid file is selected the mapping from executable to
        profile is updated.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to executable",
            util.userprofile_path(),
            "Profile (*.xml)"
        )
        if fname != "":
            self.profile_field.setText(fname)
            self.config.set_profile(
                self.executable_selection.currentText(),
                self.profile_field.text()
            )

    def _show_executable(self, exec_path):
        """Displays the profile associated with the given executable.

        :param exec_path path to the executable to shop
        """
        self.profile_field.setText(self.config.get_profile(exec_path))

    def _show_mode_change_message(self, clicked):
        """Stores the user's preference for mode change notifications.

        :param clicked whether or not the checkbox is ticked"""
        self.config.mode_change_message = clicked
        self.config.save()

    def _update_profile(self):
        """Updates the profile associated with the current executable."""
        self.config.set_profile(
            self.executable_selection.currentText(),
            self.profile_field.text()
        )


class CalibrationUi(QtWidgets.QWidget):

    """Dialog to calibrate joystick axes."""

    # Signal emitted when the dialog is being closed
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Creates the calibration UI.

        :param parent the parent widget of this object
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.devices = [
            dev for dev in util.joystick_devices() if not dev.is_virtual
        ]
        self.current_selection_id = 0

        # Create the required layouts
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.axes_layout = QtWidgets.QVBoxLayout()
        self.button_layout = QtWidgets.QHBoxLayout()

        self._create_ui()

    def _create_ui(self):
        """Creates all widgets required for the user interface."""
        # Device selection drop down
        self.device_dropdown = QtWidgets.QComboBox()
        self.device_dropdown.currentIndexChanged.connect(
            self._create_axes
        )
        for device in self.devices:
            self.device_dropdown.addItem(device.name)

        # Set the title
        self.setWindowTitle("Calibration")

        # Various buttons
        self.button_close = QtWidgets.QPushButton("Close")
        self.button_close.pressed.connect(self.close)
        self.button_save = QtWidgets.QPushButton("Save")
        self.button_save.pressed.connect(self._save_calibration)
        self.button_centered = QtWidgets.QPushButton("Centered")
        self.button_centered.pressed.connect(self._calibrate_centers)
        self.button_layout.addWidget(self.button_save)
        self.button_layout.addWidget(self.button_close)
        self.button_layout.addStretch(0)
        self.button_layout.addWidget(self.button_centered)

        # Axis widget readout headers
        self.label_layout = QtWidgets.QGridLayout()
        label_spacer = QtWidgets.QLabel()
        label_spacer.setMinimumWidth(200)
        label_spacer.setMaximumWidth(200)
        self.label_layout.addWidget(label_spacer, 0, 0, 0, 3)
        label_current = QtWidgets.QLabel("<b>Current</b>")
        label_current.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_current, 0, 3)
        label_minimum = QtWidgets.QLabel("<b>Minimum</b>")
        label_minimum.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_minimum, 0, 4)
        label_center = QtWidgets.QLabel("<b>Center</b>")
        label_center.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_center, 0, 5)
        label_maximum = QtWidgets.QLabel("<b>Maximum</b>")
        label_maximum.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_maximum, 0, 6)

        # Organizing everything into the various layouts
        self.main_layout.addWidget(self.device_dropdown)
        self.main_layout.addLayout(self.label_layout)
        self.main_layout.addLayout(self.axes_layout)
        self.main_layout.addStretch(0)
        self.main_layout.addLayout(self.button_layout)

        # Create the axis calibration widgets
        self.axes = []
        self._create_axes(self.current_selection_id)

        # Connect to the joystick events
        el = EventListener()
        el.joystick_event.connect(self._handle_event)

    def _calibrate_centers(self):
        """Records the centered or neutral position of the current device."""
        for widget in self.axes:
            widget.centered()

    def _save_calibration(self):
        """Saves the current calibration data to the hard drive."""
        cfg = config.Configuration()
        dev_id = util.device_id(
            self.devices[self.current_selection_id]
        )
        cfg.set_calibration(dev_id, [axis.limits for axis in self.axes])

    def _create_axes(self, index):
        """Creates the axis calibration widget for the current device.

        :param index the index of the currently selected device
            in the dropdown menu
        """
        widgets.clear_layout(self.axes_layout)
        self.axes = []
        self.current_selection_id = index
        for i in range(self.devices[index].axes):
            self.axes.append(widgets.AxisCalibrationWidget())
            self.axes_layout.addWidget(self.axes[-1])

    def _handle_event(self, event):
        """Process a single joystick event.

        :param event the event to process
        """
        if util.device_id(event) == util.device_id(self.devices[self.current_selection_id]) \
                and event.event_type == InputType.JoystickAxis:
            self.axes[event.identifier-1].set_current(event.raw_value)

    def closeEvent(self, event):
        """Closes the calibration window.

        :param event the close event
        """
        el = EventListener()
        el.joystick_event.disconnect(self._handle_event)
        self.closed.emit()


class AboutUi(QtWidgets.QWidget):

    """Widget which displays information about the application."""

    def __init__(self, parent=None):
        """Creates a new about widget.

        This creates a simple widget which shows version information
        and various software licenses.

        :param parent parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_About()
        self.ui.setupUi(self)

        self.ui.about.setHtml(open("about/about.html").read())

        self.ui.jg_license.setHtml(
            open("about/joystick_gremlin.html").read()
        )

        license_list = [
            "about/third_party_licenses.html",
            "about/modernuiicons.html",
            "about/pyqt.html",
            "about/pysdl2.html",
            "about/pywin32.html",
            "about/qt5.html",
            "about/sdl2.html",
            "about/vjoy.html",
            "about/mako.html",
        ]
        third_party_licenses = ""
        for fname in license_list:
            third_party_licenses += open(fname).read()
        self.ui.third_party_licenses.setHtml(third_party_licenses)


class ModeManagerUi(QtWidgets.QWidget):

    """Enables the creation of modes and configuring their inheritance."""

    # Signal emitted when mode configuration changes
    modes_changed = QtCore.pyqtSignal()

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the data being profile whose modes are being
            configured
        :param parent the parent of this wideget
        """
        QtWidgets.QWidget.__init__(self, parent)
        self._profile = profile_data
        self.setWindowTitle("Mode Manager")

        self.mode_dropdowns = {}
        self.mode_rename = {}
        self.mode_delete = {}
        self.mode_callbacks = {}

        self._create_ui()

        # Disable keyboard event handler
        el = EventListener()
        el.keyboard_hook.stop()

    def closeEvent(self, event):
        # Re-enable keyboard event handler
        el = EventListener()
        el.keyboard_hook.start()

    def _create_ui(self):
        """Creates the required UII elements."""
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.mode_layout = QtWidgets.QGridLayout()

        self.main_layout.addLayout(self.mode_layout)
        self.add_button = QtWidgets.QPushButton("Add Mode")
        self.add_button.clicked.connect(self._add_mode_cb)
        self.main_layout.addWidget(self.add_button)

        self._populate_mode_layout()

    def _populate_mode_layout(self):
        """Generates the mode layout UI displaying the different modes."""
        # Clear potentially existing content
        util.clear_layout(self.mode_layout)
        self.mode_dropdowns = {}
        self.mode_rename = {}
        self.mode_delete = {}
        self.mode_callbacks = {}

        # Obtain mode names and the mode they inherit from
        mode_list = {}
        for device in self._profile.devices.values():
            for mode in device.modes.values():
                if mode.name not in mode_list:
                    mode_list[mode.name] = mode.inherit

        # Create UI element for each mode
        row = 0
        for mode, inherit in sorted(mode_list.items()):
            self.mode_layout.addWidget(QtWidgets.QLabel(mode), row, 0)
            self.mode_dropdowns[mode] = QtWidgets.QComboBox()
            self.mode_dropdowns[mode].addItem("None")
            self.mode_dropdowns[mode].setMinimumContentsLength(20)
            for name in sorted(mode_list.keys()):
                if name != mode:
                    self.mode_dropdowns[mode].addItem(name)

            self.mode_callbacks[mode] = self._create_inheritance_change_cb(mode)
            self.mode_dropdowns[mode].currentTextChanged.connect(
                self.mode_callbacks[mode]
            )
            self.mode_dropdowns[mode].setCurrentText(inherit)

            # Rename mode button
            self.mode_rename[mode] = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_edit.png"), ""
            )
            self.mode_layout.addWidget(self.mode_rename[mode], row, 2)
            self.mode_rename[mode].clicked.connect(
                self._create_rename_mode_cb(mode)
            )
            # Delete mode button
            self.mode_delete[mode] = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/mode_delete"), ""
            )
            self.mode_layout.addWidget(self.mode_delete[mode], row, 3)
            self.mode_delete[mode].clicked.connect(
                self._create_delete_mode_cb(mode)
            )

            self.mode_layout.addWidget(self.mode_dropdowns[mode], row, 1)
            row += 1

    def _create_inheritance_change_cb(self, mode):
        """Returns a lambda function callback to change the inheritance of
        a mode.

        This is required as otherwise lambda functions created within a
        function do not behave as desired.

        :param mode the mode for which the callback is being created
        :return customized lambda function
        """
        return lambda x: self._change_mode_inheritance(mode, x)

    def _create_rename_mode_cb(self, mode):
        """Returns a lambda function callback to rename a mode.

        This is required as otherwise lambda functions created within a
        function do not behave as desired.

        :param mode the mode for which the callback is being created
        :return customized lambda function
        """
        return lambda: self._rename_mode(mode)

    def _create_delete_mode_cb(self, mode):
        """Returns a lambda function callback to delete the given mode.

        This is required as otherwise lambda functions created within a
        function do not behave as desired.

        :param mode the mode to remove
        :return lambda function to perform the removal
        """
        return lambda: self._delete_mode(mode)

    def _change_mode_inheritance(self, mode, inherit):
        """Updates the inheritance information of a given mode.

        :param mode the mode to update
        :param inherit the name of the mode this mode inherits from
        """
        # Check if this inheritance would cause a cycle, turning the
        # tree structure into a graph
        has_inheritance_cycle = False
        if inherit != "None":
            all_modes = list(self._profile.devices.values())[0].modes
            cur_mode = inherit
            while all_modes[cur_mode].inherit is not None:
                if all_modes[cur_mode].inherit == mode:
                    has_inheritance_cycle = True
                    break
                cur_mode = all_modes[cur_mode].inherit

        # Update the inheritance information in the profile
        if not has_inheritance_cycle:
            for name, device in self._profile.devices.items():
                if inherit == "None":
                    inherit = None
                device.modes[mode].inherit = inherit
            self.modes_changed.emit()

    def _rename_mode(self, mode_name):
        """Asks the user for the new name for the given mode.

        If the user provided name for the mode is invalid the
        renaming is aborted and no change made.
        """
        # Retrieve new name from the user
        name, user_input = QtWidgets.QInputDialog.getText(
                self,
                "Mode name",
                "",
                QtWidgets.QLineEdit.Normal,
                mode_name
        )
        if user_input:
            if name in util.mode_list(self._profile):
                util.display_error(
                    "A mode with the name \"{}\" already exists".format(name)
                )
            else:
                # Update the renamed mode in each device
                for device in self._profile.devices.values():
                    device.modes[name] = device.modes[mode_name]
                    device.modes[name].name = name
                    del device.modes[mode_name]

                    # Update inheritance information
                    for mode in device.modes.values():
                        if mode.inherit == mode_name:
                            mode.inherit = name

                self.modes_changed.emit()

            self._populate_mode_layout()

    def _delete_mode(self, mode_name):
        """Removes the specified mode.

        Performs an update of the inheritance of all modes that inherited
        from the deleted mode.

        :param mode_name the name of the mode to delete
        """
        # Obtain mode from which the mode we want to delete inherits
        parent_of_deleted = None
        for mode in list(self._profile.devices.values())[0].modes.values():
            if mode.name == mode_name:
                parent_of_deleted = mode.inherit

        # Assign the inherited mode of the the deleted one to all modes that
        # inherit from the mode to be deleted
        for device in self._profile.devices.values():
            for mode in device.modes.values():
                if mode.inherit == mode_name:
                    mode.inherit = parent_of_deleted

        # Remove the mode from the profile
        for device in self._profile.devices.values():
            del device.modes[mode_name]

        # Update the ui
        self._populate_mode_layout()
        self.modes_changed.emit()

    def _add_mode_cb(self, checked):
        """Asks the user for a new mode to add.

        If the user provided name for the mode is invalid no mode is
        added.
        """
        name, user_input = QtWidgets.QInputDialog.getText(None, "Mode name", "")
        if user_input:
            if name in util.mode_list(self._profile):
                util.display_error(
                    "A mode with the name \"{}\" already exists".format(name)
                )
            else:
                for device in self._profile.devices.values():
                    new_mode = profile.Mode(device)
                    new_mode.name = name
                    device.modes[name] = new_mode
                self.modes_changed.emit()

            self._populate_mode_layout()


class ModuleManagerUi(QtWidgets.QWidget):

    """UI which allows the user to manage custom python modules to
    be loaded by the program."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the profile with which to populate the ui
        :param parent the parent widget
        """
        QtWidgets.QWidget.__init__(self, parent)
        self._profile = profile_data
        self.setWindowTitle("User Module Manager")

        self._create_ui()
        # Disable keyboard event handler
        el = EventListener()
        el.keyboard_hook.stop()

    def closeEvent(self, event):
        # Re-enable keyboard event handler
        el = EventListener()
        el.keyboard_hook.start()

    def _create_ui(self):
        """Creates all the UI elements."""
        self.model = QtCore.QStringListModel()
        self.model.setStringList(sorted(self._profile.imports))

        self.view = QtWidgets.QListView()
        self.view.setModel(self.model)
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Add widgets which allow modifying the mode list
        self.add = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/macro_add.svg"), "Add"
        )
        self.add.clicked.connect(self._add_cb)
        self.delete = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/macro_delete.svg"), "Delete"
        )
        self.delete.clicked.connect(self._delete_cb)

        self.actions_layout = QtWidgets.QHBoxLayout()
        self.actions_layout.addWidget(self.add)
        self.actions_layout.addWidget(self.delete)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(self.actions_layout)

    def _add_cb(self):
        """Asks the user for the name of a new module to add to the list
        of imported modules.

        If the name is not a valid python identifier nothing is added.
        """
        new_import, input_ok = QtWidgets.QInputDialog.getText(
            self,
            "Module name",
            "Enter the name of the module to import"
        )
        if input_ok and new_import != "":
            if not util.valid_python_identifier(new_import):
                util.display_error(
                    "\"{}\" is not a valid python module name"
                    .format(new_import)
                )
            else:
                import_list = self.model.stringList()
                import_list.append(new_import)
                self.model.setStringList(sorted(import_list))
                self._profile.imports = list(import_list)

    def _delete_cb(self):
        """Removes the currently selected module from the list."""
        import_list = self.model.stringList()
        index = self.view.currentIndex().row()
        if 0 <= index <= len(import_list):
            del import_list[index]
            self.model.setStringList(import_list)
            self.view.setCurrentIndex(self.model.index(0, 0))
            self._profile.imports = list(import_list)