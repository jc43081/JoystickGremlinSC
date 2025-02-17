# -*- coding: utf-8; -*-

# Copyright (C) 2024 Jeff Cain
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

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__)))
import gremlin.profile
import mapping_reader

import logging
import threading
import time
from lxml.etree import ElementTree

from PySide6 import QtWidgets, QtCore

from gremlin.base_conditions import InputActionCondition
from gremlin.common import InputType
from gremlin import input_devices, joystick_handling, util, keyboard
from gremlin.error import ProfileError, GremlinError
from gremlin.profile import safe_format, safe_read
import gremlin.ui.ui_common
import gremlin.ui.input_item
import gremlin.ui.device_tab
from gremlin.util import *

class MapToScWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Dialog which allows the selection of a vJoy output to use as
    as the remapping for the currently selected input.
    """

    # Mapping from types to display names
    type_to_name_map = {
        InputType.JoystickAxis: "Axis",
        InputType.JoystickButton: "Button",
        InputType.JoystickHat: "Hat",
        InputType.Keyboard: "Button",
    }
    name_to_type_map = {
        "Axis": InputType.JoystickAxis,
        "Button": InputType.JoystickButton,
        "Hat": InputType.JoystickHat
    }

    def __init__(self, action_data, parent=None):
        """Creates a new MapToScWidget.

        :param action_data profile data managed by this widget
        :param parent the parent of this widget
        """
        gremlin.util.log("MapToScWidget::init " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        super().__init__(action_data, parent=parent)
        assert(isinstance(action_data, MapToSc))

    def _create_ui(self):
        gremlin.util.log("MapToScWidget::create ui " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        """Creates the UI components."""
        input_types = {
            InputType.Keyboard: [
                InputType.JoystickButton
            ],
            InputType.JoystickAxis: [
                InputType.JoystickAxis,
                InputType.JoystickButton
            ],
            InputType.JoystickButton: [
                InputType.JoystickButton
            ],
            InputType.JoystickHat: [
                InputType.JoystickButton,
                InputType.JoystickHat
            ]
        }
        self.controls_selector = ScControlsSelector(
            lambda x: self.save_controls_changes(),
            input_types[self._get_input_type()],
            self.action_data.controls_list
        )

        self.main_layout.addWidget(self.controls_selector)

        # Create UI widgets for absolute / relative axis modes if the remap
        # action is being added to an axis input type
        if self.action_data.get_input_type() == InputType.JoystickAxis:
            self.maptosc_type_widget = QtWidgets.QWidget()
            self.maptosc_type_layout = QtWidgets.QHBoxLayout(self.maptosc_type_widget)

            self.absolute_checkbox = QtWidgets.QRadioButton("Absolute")
            self.absolute_checkbox.setChecked(True)
            self.relative_checkbox = QtWidgets.QRadioButton("Relative")
            self.relative_scaling = gremlin.ui.ui_common.DynamicDoubleSpinBox()

            self.maptosc_type_layout.addStretch()
            self.maptosc_type_layout.addWidget(self.absolute_checkbox)
            self.maptosc_type_layout.addWidget(self.relative_checkbox)
            self.maptosc_type_layout.addWidget(self.relative_scaling)
            self.maptosc_type_layout.addWidget(QtWidgets.QLabel("Scale"))

            self.main_layout.addWidget(self.maptosc_type_widget)

        # Show a message when mapping a hat not within the Hat Buttons container
        if self.action_data.hardware_input_type == InputType.JoystickHat and self.action_data.parent_input_item.containers[0].tag != "hat_buttons":
            self.maptosc_hat_widget = QtWidgets.QWidget()
            self.maptosc_hat_layout = QtWidgets.QHBoxLayout(self.maptosc_hat_widget)
            self.maptosc_hat_layout.addWidget(QtWidgets.QLabel("Hats require mapping a Virtual Button. Remember to select a direction on the Virtual Button tab to the right."))
            self.main_layout.addWidget(self.maptosc_hat_widget)

        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _populate_ui(self):
        """Populates the UI components."""
        gremlin.util.log("MapToScWidget::populate ui  " + time.strftime("%a, %d %b %Y %H:%M:%S"))

        # Set the initial category and controls ids
        if (self.action_data.category_id != None):
            category_id = self.action_data.category_id
        else:
            category_id = self.controls_selector.controls_registry[0]["category_id"]
        if (self.action_data.control_id != None):
            control_id = self.action_data.control_id
        else:
            control_id = self.controls_selector.controls_registry[0]["values"][0]

        # Get the input type which can change depending on the container used
        input_type = self.action_data.input_type
        if self.action_data.parent_input_item.containers[0].tag == "hat_buttons":
            input_type = InputType.JoystickButton

        # Handle obscure bug which causes the action_data to contain no
        # input_type information
        if input_type is None:
            input_type = InputType.JoystickButton
            log_sys_warn("None as input type encountered")

        try:
            self.controls_selector.set_selection(
                input_type,
                category_id,
                control_id
            )

            if self.action_data.input_type == InputType.JoystickAxis:
                if self.action_data.axis_mode == "absolute":
                    self.absolute_checkbox.setChecked(True)
                else:
                    self.relative_checkbox.setChecked(True)
                self.relative_scaling.setValue(self.action_data.axis_scaling)

                self.absolute_checkbox.clicked.connect(self.save_controls_changes)
                self.relative_checkbox.clicked.connect(self.save_controls_changes)
                self.relative_scaling.valueChanged.connect(self.save_controls_changes)

            # Save changes so the UI updates properly
            self.save_controls_changes()
        except gremlin.error.ProfileError as e:
            util.display_error(
                f"Your profile contains a bad SC Mapping. {e}\n\n" + 
                "Check your Controls Mapping file under the Settings tab. The bad mapping " +
                "defaulted to Vehicles - Seats and Operator Modes: Emergency Exit Seat. "
            )
            log_sys_error(str(e))
        except gremlin.error.GremlinError as e:
            util.display_error(
                f"A needed vJoy device is not accessible: {e}\n\n" +
                "Default values have been set for the input, but they are "
                "not what has been specified."
            )
            log_sys_error(str(e))
        

    def save_controls_changes(self):
        """Saves UI contents to the profile data storage."""
        gremlin.util.log("MapToScWidget::save controls changes " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        # Store map to sc data
        try:
            controls_data = self.controls_selector.get_selection()
            input_type_changed = \
                self.action_data.input_type != controls_data["input_type"]
            self.action_data.category_id = controls_data["category_id"]
            self.action_data.control_id = controls_data["control_id"]
            self.action_data.input_type = controls_data["input_type"]
            self.action_data.description = controls_data["description"]
            self._update_input_item_description()

            if self.action_data.input_type == InputType.JoystickAxis:
                self.action_data.axis_mode = "absolute"
                if self.relative_checkbox.isChecked():
                    self.action_data.axis_mode = "relative"
                self.action_data.axis_scaling = self.relative_scaling.value()

            # Signal changes
            if input_type_changed:
                self.action_modified.emit()
        except gremlin.error.GremlinError as e:
            log_sys_error(str(e))


    def _update_input_item_description(self):
        update_description = False
        action_description_found = False
        # check for an action description first
        for container in self.action_data.parent_input_item.containers:
            if len(container.action_sets) > 0:
                for action_set in container.action_sets:
                    for action in action_set:
                        if action and action.name == "Description":
                            if self.action_data.parent_input_item.description != action.description:
                                self.action_data.parent_input_item.description = action.description
                                update_description = True
                            action_description_found = True
                            break

        # Use the SC Control description if its the only component
        if action_description_found == False:
            if len(self.action_data.parent_input_item.containers) == 1:
                if len(self.action_data.parent_input_item.containers[0].action_sets[0]) == 1:
                    if self.action_data.parent_input_item.description != self.action_data.description:
                        self.action_data.parent_input_item.description = self.action_data.description
                        update_description = True
                # if multiple actions available
                elif len(self.action_data.parent_input_item.containers[0].action_sets[0]) > 1:
                    self.action_data.description = "Multiple Actions Defined..."
                    self.action_data.parent_input_item.description = "Multiple Actions Defined..."
                    update_description = True
            # if multiple containers available
            elif len(self.action_data.parent_input_item.containers) > 1:
                self.action_data.description = "Multiple Actions Defined..."
                self.action_data.parent_input_item.description = "Multiple Actions Defined..."
                update_description = True

        if update_description:
            el = gremlin.event_handler.EventListener()
            el.action_description_changed.emit()


class MapToScFunctor(gremlin.base_classes.AbstractFunctor):

    """Executes a Map to Star Citizen action when called."""

    def __init__(self, action):
        super().__init__(action)
        self.vjoy_device_id = action.getVjoyDeviceId(action.category_id, action.control_id)
        self.vjoy_input_id = action.getVjoyInputId(action.category_id, action.control_id)
        self.input_type = action.input_type
        self.axis_mode = action.axis_mode
        self.axis_scaling = action.axis_scaling

        self.needs_auto_release = self._check_for_auto_release(action)
        self.thread_running = False
        self.should_stop_thread = False
        self.thread_last_update = time.time()
        self.thread = None
        self.axis_delta_value = 0.0
        self.axis_value = 0.0

        if self.input_type == InputType.JoystickAxis:
            self.device_guid = action.hardware_device.device_guid
            self.joy = input_devices.JoystickProxy()[self.device_guid]
            self.hardware_input_id = action.hardware_input_id
            if self.joy is not None:
                current_joy_value = self.joy.axis(self.hardware_input_id).value
                el = gremlin.event_handler.EventListener()                
                el.joystick_event.emit(gremlin.event_handler.Event(
                        event_type=InputType.JoystickAxis,
                        device_guid=self.device_guid,
                        identifier=self.hardware_input_id,
                        value=current_joy_value
                    ))   
                
            eh = gremlin.event_handler.EventHandler()
            eh.runtime_mode_changed.connect(self._mode_changed_cb)                

    def _mode_changed_cb(self):
            current_joy_value = self.joy.axis(self.hardware_input_id).value
            el = gremlin.event_handler.EventListener()            
            el.joystick_event.emit(gremlin.event_handler.Event(
                    event_type=InputType.JoystickAxis,
                    device_guid=self.device_guid,
                    identifier=self.hardware_input_id,
                    value=current_joy_value
                ))            


    def process_event(self, event, value):
        if self.input_type == InputType.JoystickAxis:
            if self.axis_mode == "absolute":
                joystick_handling.VJoyProxy()[self.vjoy_device_id] \
                    .axis(self.vjoy_input_id).value = value.current
            else:
                self.should_stop_thread = abs(event.value) < 0.05
                self.axis_delta_value = \
                    value.current * (self.axis_scaling / 1000.0)
                self.thread_last_update = time.time()
                if self.thread_running is False:
                    if isinstance(self.thread, threading.Thread):
                        self.thread.join()
                    self.thread = threading.Thread(
                        target=self.relative_axis_thread
                    )
                    self.thread.start()

        elif self.input_type == InputType.JoystickButton:
            if event.event_type in [InputType.JoystickButton, InputType.Keyboard] \
                    and event.is_pressed \
                    and self.needs_auto_release:

                # Release the Vjoy button
                input_devices.ButtonReleaseActions().register_button_release(
                    (self.vjoy_device_id, self.vjoy_input_id),
                    event
                )

            joystick_handling.VJoyProxy()[self.vjoy_device_id] \
                .button(self.vjoy_input_id).is_pressed = value.current
               
        elif self.input_type == InputType.JoystickHat:

            joystick_handling.VJoyProxy()[self.vjoy_device_id] \
                .button(self.vjoy_input_id).is_pressed = value.current

        return True

    def relative_axis_thread(self):
        self.thread_running = True
        vjoy_dev = joystick_handling.VJoyProxy()[self.vjoy_device_id]
        self.axis_value = vjoy_dev.axis(self.vjoy_input_id).value
        while self.thread_running:
            try:
                # If the vjoy value has was changed from what we set it to
                # in the last iteration, terminate the thread
                change = vjoy_dev.axis(self.vjoy_input_id).value - self.axis_value
                if abs(change) > 0.0001:
                    self.thread_running = False
                    self.should_stop_thread = True
                    return

                self.axis_value = max(
                    -1.0,
                    min(1.0, self.axis_value + self.axis_delta_value)
                )
                vjoy_dev.axis(self.vjoy_input_id).value = self.axis_value

                if self.should_stop_thread and \
                        self.thread_last_update + 1.0 < time.time():
                    self.thread_running = False
                time.sleep(0.01)
            except gremlin.error.VJoyError:
                self.thread_running = False

    def _check_for_auto_release(self, action):
        activation_condition = None
        if action.parent.activation_condition:
            activation_condition = action.parent.activation_condition
        elif action.activation_condition:
            activation_condition = action.activation_condition

        # If an input action activation condition is present the auto release
        # may have to be disabled
        needs_auto_release = True
        if activation_condition:
            for condition in activation_condition.conditions:
                if isinstance(condition, InputActionCondition):
                    # Remap like actions typically have an always activation
                    # condition associated with them
                    if condition.comparison != "always":
                        needs_auto_release = False

        return needs_auto_release


class MapToSc(gremlin.base_profile.AbstractAction):

    """Action remapping physical joystick inputs to Game-defined inputs."""

    name = "Map To Star Citizen"
    tag = "map-to-sc"

    default_button_activation = (True, True)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = MapToScFunctor
    widget = MapToScWidget

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the container to which this action belongs
        """
        super().__init__(parent)

        gremlin.util.log("MapToSC::Init")
        self.parent = parent
        self.input_type = self.input_item.input_type
        self.axis_mode = "absolute"
        self.axis_scaling = 1.0
        self.category_id = None
        self.control_id = None
        self.parent_input_item = parent.parent
        self.settings = parent.get_settings()
        self.description = ""

        reader = mapping_reader.ControlsMappingReader(self.settings.sc_controls_mapping)
        self.controls_list = reader.getControlsMapping()
        el = gremlin.event_handler.EventListener()
        el.controls_mapping_changed.connect(self._reload_control_list)

    def _reload_control_list(self, controls_mapping):
        reader = mapping_reader.ControlsMappingReader(controls_mapping)
        reader.resetControlsMapping(controls_mapping)

    def getVjoyDeviceId(self, category, control):
        # Make sure the mapping is valid otherwise throw an exception
        category_entry = next((x for x in self.controls_list if x["category_id"] == category), None)
        control_entry = next((x for x in category_entry["values"] if x["id"] == control), None)
        if control_entry is None:
            raise gremlin.error.GremlinError("SC Mapping is missing. Make sure your Controls Mapping file is the right version.")
        vjoy_device_id = control_entry["vjoy"]
        return vjoy_device_id

    def getVjoyInputId(self, category, control):
        category_entry = next((x for x in self.controls_list if x["category_id"] == category), None) 
        control_entry = next((x for x in category_entry["values"] if x["id"] == control), None)
        if control_entry is None:
            raise gremlin.error.GremlinError("SC Mapping is missing. Make sure your Controls Mapping file is the right version.")
        vjoy_input_type = control_entry["type"]
        if "axis" in vjoy_input_type:
            vjoy_input_id = control_entry["axis"]
        elif "button" in vjoy_input_type:
            vjoy_input_id = control_entry["button"]
        elif "hat" in vjoy_input_type:
            vjoy_input_id = control_entry["hat"]
        elif "keyboard" in vjoy_input_type:
            vjoy_input_id = control_entry["keyboard"]
        return vjoy_input_id

    def clean_up(self):
        if self.parent_input_item.description == self.description:
            self.parent_input_item.description = ""
            el = gremlin.event_handler.EventListener()
            el.action_description_changed.emit()
    

    def icon(self):
        """Returns the icon corresponding to the remapped input.

        :return icon representing the remap action
        """

        # For now, use standard icon
        return f"action_plugins/map_to_sc/icon.png"

    def requires_virtual_button(self):
        """Returns whether or not the action requires an activation condition.

        :return True if an activation condition is required, False otherwise
        """
        gremlin.util.log("MapToSC::requires_virtual_button " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        input_type = self.get_input_type()

        if input_type in [InputType.JoystickButton, InputType.Keyboard]:
            return False
        elif input_type == InputType.JoystickAxis:
            if self.input_type == InputType.JoystickAxis:
                return False
            else:
                return True
        elif input_type == InputType.JoystickHat:
            if self.input_type == InputType.JoystickHat:
                return False
            else:
                return True

    def _parse_xml(self, node):
        """Populates the data storage with data from the XML node.

        :param node XML node with which to populate the storage
        """
        gremlin.util.log("MapToSC::parse xml " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        try:
            self.category_id = safe_read(node, "category", int)
            self.control_id = safe_read(node, "controls", int)

            if self.get_input_type() == InputType.JoystickAxis and \
                    self.input_type == InputType.JoystickAxis:
                self.axis_mode = safe_read(node, "axis-type", str, "absolute")
                self.axis_scaling = safe_read(node, "axis-scaling", float, 1.0)
        except ProfileError:
            self.category_id = None
            self.control_id = None

    def _generate_xml(self):
        """Returns an XML node encoding this action's data.

        :return XML node containing the action's data
        """
        gremlin.util.log("MapToSC::generate xml " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        node = ElementTree.Element("map-to-sc")
        node.set("category", str(self.category_id))
        node.set("controls", str(self.control_id))

        if self.get_input_type() == InputType.JoystickAxis and \
                self.input_type == InputType.JoystickAxis:
            node.set("axis-type", safe_format(self.axis_mode, str))
            node.set("axis-scaling", safe_format(self.axis_scaling, float))

        return node

    def _is_valid(self):
        """Returns whether or not the action is configured properly.

        :return True if the action is configured correctly, False otherwise
        """
        gremlin.util.log("MapToSC::is valid " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        return not(self.category_id is None or self.control_id is None)              


class ScControlsSelector(QtWidgets.QWidget):

    """
        Create a Selector that can allows for managing a category and 
        the allowed controls within that category.
    
        Category will provide the valid list of controls.
        Controls will be mapped to proper vJoy Device and Input
    """

    def __init__(self, change_cb, valid_types, control_list, parent=None):
        super().__init__(parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        gremlin.util.log("ControlsSelector::init: " + time.strftime("%a, %d %b %Y %H:%M:%S"))

        self.change_cb = change_cb

        if InputType.JoystickAxis in valid_types:
            self.current_input_type = "axis"
        elif InputType.JoystickButton in valid_types:
            self.current_input_type = "button"
        elif InputType.JoystickHat in valid_types:
            self.current_input_type = "hat"
        elif InputType.Keyboard in valid_types:
            self.current_input_type = "button"
        else:
            self.current_input_type = "unknown"
        self.valid_types = valid_types

        self.controls_list = control_list

        self.category_dropdown = None
        self.controls_dropdown = []
        self._category_registry = []
        self.controls_registry = []

        self._create_controls_dropdown()

    def get_selection(self):
        gremlin.util.log("ControlsSelector::get selection: " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        category_id = None
        control_id = None
        input_type = None

        # Retrieve the IDs for the category and control
        # First get the Category Id and corresponding control list from registry using the dropdown index
        category_id = self._category_registry[self.category_dropdown.currentIndex()]
        category_control_list = next((x for x in self.controls_registry if x["category_id"] == category_id), None)

        # Then get the control Id using the control index from the dropdown (index is based on selected category)
        control_index = self.controls_dropdown[self.category_dropdown.currentIndex()].currentIndex()
        if control_index < 0: control_index = 0
        control_id = category_control_list["values"][control_index]

        # Finally get the selected control from the controls list
        category_entry = next((x for x in self.controls_list if x["category_id"] == category_id), None) 
        control_entry = next((x for x in category_entry["values"] if x["id"] == control_id), None)  

        # vJoy fields will be obtained on the fly from the Control Mapping
                 
        input_type = self.valid_types[0]
        description =  control_entry["name"]

        return {
            "category_id": category_id,
            "control_id": control_id,
            "input_type": input_type,
            "description": description
        }

    def set_selection(self, input_type, category_id, control_id):
        gremlin.util.log("ControlsSelector::set selection: " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        if category_id not in self._category_registry:
            raise ProfileError(f"Bad Mapping - Category Id: {category_id}, Control Id: {control_id} ")

        control = next((x for x in self.controls_list if x["category_id"] == category_id), None)
        if next((x for x in control["values"] if x["id"] == control_id), None) == None:
            raise ProfileError(f"Bad Mapping - Category Id: {category_id}, Control Id: {control_id} ")

        # # Get the index of the combo box associated with this category
        category_index = [index for (index, category) in enumerate(self._category_registry) if category == category_id][0]

        # Select and display correct combo boxes and entries within
        self.category_dropdown.setCurrentIndex(category_index)

        # Retrieve the index of the correct entry in the combobox
        category_control_list = next((x for x in self.controls_registry if x["category_id"] == category_id), None)
        control_index = [index for (index, value) in enumerate(category_control_list["values"]) if value == control_id][0]

        # Select and display correct combo boxes and entries within
        for entry in self.controls_dropdown:
            entry.setVisible(False)
        self.controls_dropdown[category_index].setCurrentIndex(control_index)
        self.controls_dropdown[category_index].setVisible(True)

    def _update_category(self, index):
        gremlin.util.log("ControlsSelector::update category: " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        # Hide all selection dropdowns
        for entry in self.controls_dropdown:
            entry.setVisible(False)

        # Show the first item in the new category
        self.controls_dropdown[index].setVisible(True)
        self.controls_dropdown[index].setCurrentIndex(0)
        self._execute_callback()


    def _create_controls_dropdown(self):
        gremlin.util.log("ControlsSelector::create controls dropdown: " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        self.controls_dropdown = []
        self.controls_registry = []

        # Prepare the registries (they hold IDs for combo boxes)
        for category in self.controls_list:
            self._category_registry.append(category["category_id"])

        for category in self.controls_list:
            self.controls_registry.append({ "category_id": category["category_id"], "values": [] })

            for control in category["values"]:
                if control["type"] == self.current_input_type:
                    self.controls_registry[-1]["values"].append(control["id"])

            if len(self.controls_registry[-1]["values"]) == 0:
                self._category_registry.remove(category["category_id"])
                self.controls_registry.pop()

        # create the category dropdown widgets
        self.label = QtWidgets.QLabel("Category:")
        self.main_layout.addWidget(self.label)                
        self.category_dropdown = QtWidgets.QComboBox(self)
        for category_id in self._category_registry:
            category = next((x for x in self.controls_list if x["category_id"] == category_id), None)
            self.category_dropdown.addItem(category["name"])
            self.main_layout.addWidget(self.category_dropdown)
            self.category_dropdown.activated.connect(self._update_category)

        try:
            # Create controls selections for the category. Each selection
            # will be invisible unless it is selected as the active category
            self.label = QtWidgets.QLabel("Control:")
            self.main_layout.addWidget(self.label)               
            for category in self.controls_registry:
                selection = QtWidgets.QComboBox(self)
                selection.setMaxVisibleItems(len(category["values"]))
                
                # Add items based on the controls type
                for control in category["values"]:
                    category_entry = next((x for x in self.controls_list if x["category_id"] == category["category_id"]), None) 
                    control_entry = next((x for x in category_entry["values"] if x["id"] == control), None) 
                    selection.addItem(control_entry["name"])

                # Add the controls selection and hide it
                selection.setVisible(False)
                selection.activated.connect(self._execute_callback)
                self.main_layout.addWidget(selection)
                self.controls_dropdown.append(selection)
                selection.currentIndexChanged.connect(self._execute_callback)
        except:
            util.display_error("Controls Mapping is invalid. Please check the file and restart Joystick Gremlin.")
            raise GremlinError(
                "Unable to build Controls Dropdown. Failed on: Category - " + str(category["category_id"])
            )

        # Choose first entry by default
        self.controls_dropdown[0].setVisible(True)

    def _execute_callback(self):
        gremlin.util.log("ControlsSelector::execute callback: " + time.strftime("%a, %d %b %Y %H:%M:%S"))
        self.change_cb(self.get_selection())

version = 1
name = "map-to-sc"
create = MapToSc
