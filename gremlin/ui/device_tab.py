# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott - Modified by Muchimi (C) EMCS 2024 and other contributors
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


import logging

from PySide6 import QtWidgets, QtCore

import container_plugins.basic
import gremlin
from gremlin.common import DeviceType, InputType
from . import common, input_item
from gremlin.keyboard import Key


class InputItemConfiguration(QtWidgets.QFrame):

    """UI dialog responsible for the configuration of a single
    input item such as an axis, button, hat, or key.
    """

    # Signal emitted when the description changes
    description_changed = QtCore.Signal(str)

    def __init__(self, item_data, parent=None):
        """Creates a new object instance.

        :param item_data profile data associated with the item
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.item_data = item_data

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.button_layout = QtWidgets.QHBoxLayout()
        self.widget_layout = QtWidgets.QVBoxLayout()

        self._create_description()
        if self.item_data.parent.parent.type == gremlin.common.DeviceType.VJoy:
            self._create_vjoy_dropdowns()
        else:
            self._create_dropdowns()

        self.action_model = ActionContainerModel(self.item_data.containers)
        self.action_view = ActionContainerView()
        self.action_view.set_model(self.action_model)
        self.action_view.redraw()

        self.main_layout.addWidget(self.action_view)

        # setup the container widget reference
        plugin_manager = gremlin.plugin_manager.ContainerPlugins()
        plugin_manager.set_widget(self.item_data, self)
        

    def _add_action(self, action_name):
        """Adds a new action to the input item.

        :param action_name name of the action to be added
        """
        # If this is a vJoy item then do not permit adding an action if
        # there is already one present, as only response curves can be added
        # and only one of them makes sense to exist
        if self.item_data.get_device_type() == DeviceType.VJoy:
            if len(self.item_data.containers) > 0:
                return

        plugin_manager = gremlin.plugin_manager.ActionPlugins()
        container = container_plugins.basic.BasicContainer(self.item_data)
        container.add_action(
            plugin_manager.get_class(action_name)(container)
        )

        # add the container
        #self.item_data.containers.append(container)

        if len(container.action_sets) > 0:
            self.action_model.add_container(container)
        
        self.action_model.data_changed.emit()

    def _paste_action(self, action):
        """ paste action to the input item """
        if self.item_data.get_device_type() == DeviceType.VJoy:
            if len(self.item_data.containers) > 0:
                return

        plugin_manager = gremlin.plugin_manager.ActionPlugins()
        action_item = plugin_manager.duplicate(action)
        container = container_plugins.basic.BasicContainer(self.item_data)
        container.add_action(action_item)
        
        if len(container.action_sets) > 0:
            self.action_model.add_container(container)
        self.action_model.data_changed.emit()        

    def _add_container(self, container_name):
        """Adds a new container to the input item.

        :param container_name name of the container to be added
        """
        plugin_manager = gremlin.plugin_manager.ContainerPlugins()
        container = plugin_manager.get_class(container_name)(self.item_data)
        if hasattr(container, "action_model"):
            container.action_model = self.action_model
        self.action_model.add_container(container)
        plugin_manager.set_container_data(self.item_data, container)
        return container
    

    def _paste_container(self, container):
        """Adds a new container to the input item.

        :param container container to be added
        """
        plugin_manager = gremlin.plugin_manager.ContainerPlugins()
        container_item = plugin_manager.duplicate(container)
        if hasattr(container_item, "action_model"):
            container_item.action_model = self.action_model
        self.action_model.add_container(container_item)
        plugin_manager.set_container_data(self.item_data, container_item)
        return container_item    

    def _remove_container(self, container):
        """Removes an existing container from the InputItem.

        :param container the container instance to be removed
        """
        self.action_model.remove_container(container)

    def _create_description(self):
        """Creates the description input for the input item."""
        self.description_layout = QtWidgets.QHBoxLayout()
        self.description_layout.addWidget(
            QtWidgets.QLabel("<b>Action Description</b>")
        )
        self.description_field = QtWidgets.QLineEdit()
        self.description_field.setText(self.item_data.description)
        self.description_field.textChanged.connect(self._edit_description_cb)
        self.description_layout.addWidget(self.description_field)

        self.main_layout.addLayout(self.description_layout)

    def _create_dropdowns(self):
        """Creates a drop down selection with actions that can be
        added to the current input item.
        """
        self.action_layout = QtWidgets.QHBoxLayout()

        self.action_selector = gremlin.ui.common.ActionSelector(
            self.item_data.input_type
        )
        self.action_selector.action_added.connect(self._add_action)
        self.action_selector.action_paste.connect(self._paste_action)

        self.container_selector = input_item.ContainerSelector(
            self.item_data.input_type
        )
        self.container_selector.container_added.connect(self._add_container)
        self.container_selector.container_paste.connect(self._paste_container)
        self.always_execute = QtWidgets.QCheckBox("Always execute")
        self.always_execute.setChecked(self.item_data.always_execute)
        self.always_execute.stateChanged.connect(self._always_execute_cb)

        self.action_layout.addWidget(self.action_selector)
        self.action_layout.addWidget(self.container_selector)
        self.action_layout.addWidget(self.always_execute)
        self.main_layout.addLayout(self.action_layout)

    def _create_vjoy_dropdowns(self):
        """Creates the action drop down selection for vJoy devices."""
        self.action_layout = QtWidgets.QHBoxLayout()

        self.action_selector = gremlin.ui.common.ActionSelector(
            gremlin.common.DeviceType.VJoy
        )
        self.action_selector.action_added.connect(self._add_action)
        self.action_selector.action_paste.connect(self._paste_action)
        self.action_layout.addWidget(self.action_selector)
        self.main_layout.addLayout(self.action_layout)

    def _edit_description_cb(self, text):
        """Handles changes to the description text field.

        :param text the new contents of the text field
        """
        self.item_data.description = text
        self.description_changed.emit(text)

    def _always_execute_cb(self, state):
        """Handles changes to the always execute checkbox.

        :param state the new state of the checkbox
        """
        self.item_data.always_execute = self.always_execute.isChecked()

    def _valid_action_names(self):
        """Returns a list of valid actions for this InputItemWidget.

        :return list of valid action names
        """
        action_names = []
        if self.item_data.input_type == gremlin.common.DeviceType.VJoy:
            entry = gremlin.plugin_manager.ActionPlugins().repository.get(
                "response-curve",
                None
            )
            if entry is not None:
                action_names.append(entry.name)
            else:
                raise gremlin.error.GremlinError(
                    "Response curve plugin is missing"
                )
        else:
            for entry in gremlin.plugin_manager.ActionPlugins().repository.values():
                if self.item_data.input_type in entry.input_types:
                    action_names.append(entry.name)
        return sorted(action_names)


class ActionContainerModel(common.AbstractModel):

    """Stores action containers for display using the corresponding view."""

    def __init__(self, containers, parent=None):
        """Creates a new instance.

        :param containers the container instances of this model
        :param parent the parent of this widget
        """
        super().__init__(parent)
        self._containers = containers

    def rows(self):
        """Returns the number of rows in the model.

        :return number of rows in the model
        """
        return len(self._containers)

    def data(self, index):
        """Returns the data stored at the given location.

        :param index the location for which to return data
        :return the data stored at the requested location
        """
        assert len(self._containers) > index
        return self._containers[index]

    def add_container(self, container):
        """Adds a container to the model.

        :param container the container instance to be added
        """
        self._containers.append(container)
        self.data_changed.emit()

    def remove_container(self, container):
        """Removes an existing container from the model.

        :param container the container instance to remove
        """
        if container in self._containers:
            del self._containers[self._containers.index(container)]
        self.data_changed.emit()


class ActionContainerView(common.AbstractView):

    """View class used to display ActionContainerModel contents."""

    def __init__(self, parent=None):
        """Creates a new view instance.

        :param parent the parent of the widget
        """
        super().__init__(parent)

        # Create required UI items
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()

        # Configure the widget holding the layout with all the buttons
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        # Configure the scroll area
        self.scroll_area.setMinimumWidth(800)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

    def redraw(self):
        """Redraws the entire view."""
        common.clear_layout(self.scroll_layout)
        for index in range(self.model.rows()):
            widget = self.model.data(index).widget(self.model.data(index))
            widget.closed.connect(self._create_closed_cb(widget))
            widget.container_modified.connect(self.model.data_changed.emit)
            self.scroll_layout.addWidget(widget)
        self.scroll_layout.addStretch(1)

    def _create_closed_cb(self, widget):
        """Create callbacks to remove individual containers from the model.

        :param widget the container widget to be removed
        :return callback function to remove the provided widget from the
            model
        """
        return lambda: self.model.remove_container(widget.profile_data)


class JoystickDeviceTabWidget(QtWidgets.QWidget):

    """Widget used to configure a single device."""

    def __init__(
            self,
            device,
            device_profile,
            current_mode,
            parent=None
    ):
        """Creates a new object instance.

        :param device device information about this widget's device
        :param device_profile profile data of the entire device
        :param current_mode currently active mode
        :param parent the parent of this widget
        """
        super().__init__(parent)

        # Store parameters
        self.device_profile = device_profile
        self.current_mode = current_mode

        self.device = device
        self.last_item_data = None

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.left_panel_layout = QtWidgets.QVBoxLayout()
        self.device_profile.ensure_mode_exists(self.current_mode, self.device)

        # List of inputs
        self.input_item_list_model = input_item.InputItemListModel(
            device_profile,
            current_mode
        )
        self.input_item_list_view = input_item.InputItemListView(name=device.name)
        self.input_item_list_view.setMinimumWidth(375)
        

        # Handle vJoy as input and vJoy as output devices properly
        vjoy_as_input = self.device_profile.parent.settings.vjoy_as_input

        # For vJoy as output only show axes entries, for all others treat them
        # as if they were physical input devices
        if device.is_virtual and not vjoy_as_input.get(device.vjoy_id, False):
            self.input_item_list_view.limit_input_types([InputType.JoystickAxis])
        self.input_item_list_view.set_model(self.input_item_list_model)

        self.input_item_list_view.redraw()
    

        # Handle user interaction
        self.input_item_list_view.item_selected.connect(
            self.input_item_selected_cb
        )

        # Add modifiable device label
        label_layout = QtWidgets.QHBoxLayout()
        label_layout.setContentsMargins(10, 9, 9, 0)
        label_layout.addWidget(QtWidgets.QLabel("<b>Device Label</b>"))
        line_edit = QtWidgets.QLineEdit()
        line_edit.setText(device_profile.label)
        line_edit.textChanged.connect(self.update_device_label)
        label_layout.addWidget(line_edit)

        self.left_panel_layout.addLayout(label_layout)
        self.left_panel_layout.addWidget(self.input_item_list_view)

        # Add a help text for the purpose of the vJoy tab
        if device is not None and \
                device.is_virtual and \
                not vjoy_as_input.get(device.vjoy_id, False):
            label = QtWidgets.QLabel(
                "This tab allows assigning a response curve to virtual axis. "
                "The purpose of this is to enable split and merge axis to be "
                "customized to a user's needs with regards to dead zone and "
                "response curve."
            )
            label.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
            label.setWordWrap(True)
            label.setFrameShape(QtWidgets.QFrame.Box)
            label.setMargin(10)
            self.left_panel_layout.addWidget(label)

        self.main_layout.addLayout(self.left_panel_layout)


        # listen to device changes
        el = gremlin.event_handler.EventListener()
        el.joystick_event.connect(self._device_update)
        el.profile_start.connect(self._profile_start)
        el.profile_stop.connect(self._profile_stop)

        self.running = False
        self.updating = False
        self.last_event = None

    def _device_update(self, event):
        if self.running:
            return 

        if self.last_event == event:
            return
        
        self.last_event = event
        if self.device.device_guid != event.device_guid:
            return
                
        if event.event_type == gremlin.common.InputType.JoystickButton:
            if not event.is_pressed:
                return
        elif event.event_type == gremlin.common.InputType.JoystickAxis:
            cfg = gremlin.config.Configuration()
            if not cfg.highlight_input:
                return
            if not gremlin.input_devices.JoystickInputSignificant().should_process(event):
                return
        elif event.event_type == gremlin.common.InputType.JoystickHat:
            if not event.is_pressed:
                return

        self.input_item_list_view.select_input(event.event_type, event.identifier)

        

    def _profile_start(self):
        self.running = True

    def _profile_stop(self):
        self.running = False

    def input_item_selected_cb(self, index):
        """Handles the selection of an input item.

        :param index the index of the selected item
        """
        item_data = input_item_index_lookup(
            index,
            self.device_profile.modes[self.current_mode]
        )

        if self.last_item_data == item_data:
            return
        self.last_item_data = item_data

        # Remove the existing widget, if there is one
        item = self.main_layout.takeAt(1)
        if item is not None and item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        if item:
            self.main_layout.removeItem(item)

        if item_data is not None:
            widget = InputItemConfiguration(item_data)
            change_cb = self._create_change_cb(index)
            widget.action_model.data_changed.connect(change_cb)
            widget.description_changed.connect(change_cb)

            self.main_layout.addWidget(widget)
            
    def set_mode(self, mode):
        ''' changes the mode of the tab '''

        if self.current_mode == mode:
            # nothing to do
            return 
            
        self.current_mode = mode
        self.device_profile.ensure_mode_exists(self.current_mode, self.device)
        

        # Remove the existing widget, if there is one
        item = self.main_layout.takeAt(1)
        if item is not None and item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        if item:
            self.main_layout.removeItem(item)


        self.input_item_list_model.mode = mode            

        # Select the first input item
        self.input_item_list_view.select_item(0, emit_signal=False)


    def mode_changed_cb(self, mode):
        """Handles mode change.

        :param mode the new mode
        """
        self.set_mode(mode)
        
    def refresh(self):
        """Refreshes the current selection, ensuring proper synchronization."""
        if self.input_item_list_view.current_index is not None:
            self.input_item_selected_cb(self.input_item_list_view.current_index)

    def _create_change_cb(self, index):
        """Creates a callback handling content changes.

        :param index the index of the content being changed
        :return callback function redrawing changed content
        """
        return lambda: self.input_item_list_view.redraw_index(index)

    def update_device_label(self, text):
        """Updates the label assigned to this device.

        :param text the new label text
        """
        self.device_profile.label = text


class KeyboardDeviceTabWidget(QtWidgets.QWidget):

    """Widget used to configure a single device."""

    def __init__(
            self,
            device_profile,
            current_mode,
            parent=None
    ):
        """Creates a new object instance.

        :param device_profile profile data of the entire device
        :param current_mode currently active mode
        :param parent the parent of this widget
        """
        super().__init__(parent)

        # Store parameters
        self.device_profile = device_profile
        self.current_mode = current_mode

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.left_panel_layout = QtWidgets.QVBoxLayout()
        self.device_profile.ensure_mode_exists(self.current_mode)
        self.widget_storage = {}

        # List of inputs
        self.input_item_list_model = input_item.InputItemListModel(
            device_profile,
            current_mode
        )
        self.input_item_list_view = input_item.InputItemListView()
        self.input_item_list_view.setMinimumWidth(350)

        # Input type specific setups
        self.input_item_list_view.set_model(self.input_item_list_model)
        

        # TODO: make this saner
        self.input_item_list_view.redraw()

        # Handle user interaction
        self.input_item_list_view.item_selected.connect(
            self.input_item_selected_cb
        )

        self.left_panel_layout.addWidget(self.input_item_list_view)
        self.main_layout.addLayout(self.left_panel_layout)

        button_container_widget = QtWidgets.QWidget()
        button_container_layout = QtWidgets.QHBoxLayout()
        button_container_widget.setLayout(button_container_layout)

        # key clear button
        
        clear_keyboard_button = common.ConfirmPushButton("Clear Keys", show_callback = self._show_clear_cb)
        clear_keyboard_button.confirmed.connect(self._clear_keys_cb)
        button_container_layout.addWidget(clear_keyboard_button)
        button_container_layout.addStretch(1)

        # Key add button
        button = common.NoKeyboardPushButton("Add Key")
        button.clicked.connect(self._record_keyboard_key_cb)

        button_container_layout.addWidget(button)
        

        virtual_keyboard_button = QtWidgets.QPushButton("Select Key")
        virtual_keyboard_button.clicked.connect(self._select_keys_cb)
        button_container_layout.addWidget(virtual_keyboard_button)
        

        self.left_panel_layout.addWidget(button_container_widget)
        

        # Select first entry by default
        self.input_item_selected_cb(0)

    def _show_clear_cb(self):
        return self.input_item_list_model.keyboard_rows > 0

    def _clear_keys_cb(self):
        ''' clears keyboard input keys '''

        self.input_item_list_model.clear()
        self.input_item_list_view.redraw()

    def _select_keys_cb(self):
        ''' display the keyboard input dialog '''
        from gremlin.ui.virtual_keyboard import InputKeyboardDialog
        self._keyboard_dialog = InputKeyboardDialog(parent = self, select_single = True)
        self._keyboard_dialog.accepted.connect(self._keyboard_dialog_ok_cb)
        self._keyboard_dialog.showNormal()  

    def _keyboard_dialog_ok_cb(self):
        ''' callled when the dialog completes '''

        # grab the new data
        keys = self._keyboard_dialog.keys
        if keys:
            modifiers = []
            root_key = None
            for key in keys:
                if key.is_modifier:
                    modifiers.append(key)
                else:
                    root_key = key
            if modifiers:
                root_key.latched_keys = modifiers
            self._add_keyboard_key_cb(root_key)
                  

    def input_item_selected_cb(self, index):
        """Handles the selection of an input item.

        :param index the index of the selected item
        """
        # Assumption is that the entries are sorted by their scancode and
        # extended flag identification
        # sorted_keys = sorted(self.device_profile.modes[self.current_mode].config[InputType.Keyboard])
        sorted_keys = list(self.device_profile.modes[self.current_mode].config[InputType.Keyboard])

        if index is None or len(sorted_keys) <= index:
            return
        index_key = sorted_keys[index]
        item_data = self.device_profile.modes[self.current_mode]. \
            config[InputType.Keyboard][index_key]
        
        # Remove the existing widget, if there is one
        item = self.main_layout.takeAt(1)
        if item is not None and item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        if item:
            self.main_layout.removeItem(item)

        # Create new configuration widget
        widget = InputItemConfiguration(item_data)
        change_cb = self._create_change_cb(self._index_for_key(index_key))
        widget.action_model.data_changed.connect(change_cb)
        widget.description_changed.connect(change_cb)

        self.main_layout.addWidget(widget)

        # Refresh item list view and select correct entry
        self.input_item_list_view.redraw()
        self.input_item_list_view.select_item(
            self._index_for_key(index_key),
            False
        )

    def _record_keyboard_key_cb(self):
        """Handles adding of new keyboard keys to the list.

        Asks the user to press the key they wish to add bindings for.
        """
        self.button_press_dialog = common.InputListenerWidget(
            self._add_keyboard_key_cb,
            [gremlin.common.InputType.Keyboard],
            return_kb_event=False,
            multi_keys=False
        )

        # Display the dialog centered in the middle of the UI
        root = self
        while root.parent():
            root = root.parent()
        geom = root.geometry()

        self.button_press_dialog.setGeometry(
            int(geom.x() + geom.width() / 2 - 150),
            int(geom.y() + geom.height() / 2 - 75),
            300,
            150
        )
        self.button_press_dialog.show()

    def _add_keyboard_key_cb(self, key : Key):
        """Adds the provided key to the list of keys.

        :param key the new key to add, either a single key or a combo-key

        """

        # ensure there's an entry for the 
        self.device_profile.modes[self.current_mode].get_data(gremlin.common.InputType.Keyboard,key)
        self.input_item_list_view.redraw()
        self.input_item_list_view.select_item(self._index_for_key(key),True)

    def _index_for_key(self, key):
        """Returns the index into the key list based on the key itself.

        :param key the keyboard key being queried
        :return index of the provided key
        """
        mode = self.device_profile.modes[self.current_mode]
        #sorted_keys = sorted(mode.config[InputType.Keyboard])
        sorted_keys = list(mode.config[InputType.Keyboard])
        return sorted_keys.index(key)

    def _create_change_cb(self, index):
        """Creates a callback handling content changes.

        :param index the index of the content being changed
        :return callback function redrawing changed content
        """
        return lambda: self.input_item_list_view.redraw_index(index)

    def set_mode(self, mode):
        ''' changes the mode of the tab '''        
        self.current_mode = mode
        self.device_profile.ensure_mode_exists(self.current_mode)
        self.input_item_list_model.mode = mode

        # Remove the existing widget, if there is one
        item = self.main_layout.takeAt(1)
        if item is not None and item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        if item:
            self.main_layout.removeItem(item)

    def mode_changed_cb(self, mode):
        """Handles mode change.

        :param mode the new mode
        """
        self.set_mode(mode)


    def refresh(self):
        """Refreshes the current selection, ensuring proper synchronization."""
        self.input_item_selected_cb(self.input_item_list_view.current_index)


def input_item_index_lookup(index, input_items):
    """Returns the profile data belonging to the provided index.

    This function determines which actual input item a given index refers to
    and then returns the content for it.

    :param index the index for which to return the data
    :param input_items the profile data from which to return the data
    :return profile data corresponding to the provided index
    """
    axis_count = len(input_items.config[InputType.JoystickAxis])
    button_count = len(input_items.config[InputType.JoystickButton])
    hat_count = len(input_items.config[InputType.JoystickHat])
    key_count = len(input_items.config[InputType.Keyboard])

    if key_count > 0:
        if not input_items.has_data(InputType.Keyboard, index):
            logging.getLogger("system").error(
                "Attempting to retrieve non existent input, "
                f"type={InputType.to_string(InputType.Keyboard)} index={index}"
            )
        return input_items.get_data(InputType.Keyboard, index)
    else:
        if index < axis_count:
            # Handle non continuous axis setups
            axis_keys = sorted(input_items.config[InputType.JoystickAxis].keys())
            if not input_items.has_data(InputType.JoystickAxis, axis_keys[index]):
                logging.getLogger("system").error(
                    "Attempting to retrieve non existent input, "
                    f"type={InputType.to_string(InputType.JoystickAxis)} index={axis_keys[index]}"
                )

            return input_items.get_data(
                InputType.JoystickAxis,
                axis_keys[index]
            )
        elif index < axis_count + button_count:
            if not input_items.has_data(
                    InputType.JoystickButton,
                    index - axis_count + 1
            ):
                logging.getLogger("system").error(
                    "Attempting to retrieve non existent input, "
                    f"type={InputType.to_string(InputType.JoystickButton)} index={index - axis_count + 1}"
                )

            return input_items.get_data(
                InputType.JoystickButton,
                index - axis_count + 1
            )
        elif index < axis_count + button_count + hat_count:
            if not input_items.has_data(
                    InputType.JoystickHat,
                    axis_count + button_count + hat_count
            ):
                logging.getLogger("system").error(
                    "Attempting to retrieve non existent input, "
                    f"type={ InputType.to_string(InputType.JoystickHat)} index={index - axis_count - button_count + 1}"
                )

            return input_items.get_data(
                InputType.JoystickHat,
                index - axis_count - button_count + 1
            )
