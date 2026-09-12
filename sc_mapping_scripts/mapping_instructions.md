# SC Mapping Intro

To make Joystick Gremlin SC work correctly, the internal mappings need to updated when Star Citizen adds, updates or deletes bindings. Below are the instructions on how to accomplish this. To better understand the instructions, you need to understand the files being used.

_Star Citizen Control Profile (typically layout_JG_StarCitizenMapping_x-x-x_exported.xml):_ This file has the control bindings used within Star Citizen and are imported/exported using Custom Profile function within Keybindings

_Joystick Gremlin SC Controls Mapping:_ This file contains the mapping between your joysticks and the Star Citizen control. It mirrors the options available in Star Citizen and is what is seen within the 'Map to SC' mapping in JG. 

_vjoynumbering.py:_ This script will run through the SC Controls Mapping file and renumber all the controls to the Vjoy buttons and axises

_generate_actionmap.py:_ This script takes the SC Controls Mapping file and generates an updated Star Citizen Control Profile to be imported to Star Citizen

_layout_template.xml:_ This is template used by the 'generate_actionma' script when creating the Star Citizen Control Profile. It is setup for 5 vjoys and will need expanded if more vjoys become required.

# SC Mapping Instructions

Star Citizen Controls are managed in a file called "actionmaps.xml" under _live/user/client/0/Profiles/default_. This file is used by the game to determine the mappings to use and has mappings for keyboard, mouse, gamepads, and joysticks. Updating this actionmaps.xml file is best done using Star Citizen's Keybindings function within the Options menu. Exporting a custom Control Profile produces a copy of the actionsmap.xml file with your specific mappings. Star Citizen outlines how to do this in their articled titled [Create, Export and Import Custom Profiles](https://support.robertsspaceindustries.com/hc/en-us/articles/360000183328-Create-export-and-import-custom-profiles)

Joystick Gremlin SC maintains a custom actionmaps.xml file that is imported through the Control Profiles function within Star Citizen's Keybindings menu. The Joystick Gremlin SC Controls Mapping file must be updated each time the controls change in Star Citizen. To do this, you need to capture any new or changed bindings, compare to the old bindings and then update the Mapping file to align with the changes. 

To do this, follow these directions:

1. Go into the Star Citizen and open the Keybindings within the Options menu.
2. Go to Customizations and switch to 'Joystick'. 
3. If needed, import the latest Joystick Gremlin SC Control Profile (typically 'layout_JG_StarCitizenMapping_x-x-x_exported.xml") into Star Citizen.
4. Go through each Category and add a binding for any missing controls. It is recommended to use the same button or axis for each new mapping so they are easy to find in later steps. NOTE: Some categories were skipped since they weren't related to ship controls (ex. On Foot). An alternative Control Profile with Onfoot is available but it requires 6 vjoys instead of 5.
5. Once all controls have a binding, export the bindings into a new Control Profile. Recommended you follow the same filename pattern.
8. Copy the new Control Profile file into the _sc_mapping_scripts_ directory.
9. Open the new Control Profile file and then open a compare window against the previous Control Profile.
10. Make a copy of the SC Controls Mapping file (in the _control_mappings_ directory) and follow the naming scheme incrementing for the Star Citizen version.
11. Open this new SC Controls Mapping file.
12. With this setup, you will need to review each category within the Control Profile comparison to determine if any changes have occurred.
13. If changes are required, follow this scheme to update the SC Controls Mapping file to reflect the changes in the Control Profile:
       * _Added Category:_ Add a new entry in the appropriate place in the file. Create a unique category_id and number it so it matches the order in SC. Leave space between numbers in case new categories are added later.
       * _Updated Category:_ If the name was updated, simply update the name
       * _Removed Category:_ If a category was removed, update the name to indicate where the controls moved to. Then update each entry under values by changing the name to "Remap - Control No Longer Available" and adding a "disabled" attribute set to true. This allows the user to see that the control needs remapped but doesn't list them as available controls.
       * _Added Entry:_ Add a new entry under the appropriate category (copy from an existing one). Place the entry so the order matches the selection in the SC menu. Update the fields per below:
         * Name: Match what is in SC
         * Id: Make the ID unique and within the order of the existing file. If possible, leave room for additional entries.
         * Type: Either "button" or "axis"
         * Actionmap: Find the entry in the "actionsmap.xml" file and put in the value. This matches the category in the menu.
         * Action: Find the entry under the actionmap that matches the specific mapping. Sometimes it's not clear and you may have to manually map it to something unique and then export a new control profile to identify which action is correct.
         * vjoy, axis and button are automatically assigned so no need to update or assign
       * _Updated Entry:_ Sometimes the name will change and you'll need to update the name under the appropriate entry. Additionally, the action can change and will need to be updated.
       * _Removed Entry:_ Update the name to reflect the need to remap. Either use "Remap - Control No Longer Available" or "Remap - Control moved to XXX category". This indicates to the user that the mapping is no longer valid and needs to be remapped.


Once the SC Controls Mapping file has been updated, the vjoy, axis and button values need to be automatically generated. To do this, do the following:
1. Open the _vjoynumbering.py_ in the "sc_mapping_scripts" directory. 
2. Update the name of the _controls_mapping_ variable to reflect the name of the new mapping file created above. 
3. Open a command prompt and change directories to the "sc_mapping_scripts" directory
4. Use the command "python vjoynumbering.py" to generate a new mapping file. A new file is created that ends in ".mapped" in order to avoid overwriting the original in case something goes wrong. 
5. Validate that the number vjoys is not more than 5. If so, updates will be required to the setup documentation, the layout_template, and the generate_actionmap script
6. Check the new file to ensure everything worked and if correct, replace the original file with this new version.

With the Control Mappings file updated with appropriate vjoy, axis and button values, the SC Control Profile needs to be generated. This is the file imported into Star Citizen by the user. To generate this file, do the following:
1. Open the _generate_actionmap.py_ in the "sc_mapping_scripts" directory. 
2. Update the _version_ variable to reflect the version used in the Control Mapping file above.
3. Update the directory variables to match your configuration.
4. Open a command prompt and change directories to the "sc_mapping_scripts" directory
5. Use the command "python generate_actionmap.py" to generate a new Control Profile file.

In the end, the SC Controls Mapping file (json) needs to be in the "controls_mapping" directory and a new version of Joystick Gremlin SC will need to be released to include it. Additionally, the new SC Control Profile (xml) will be generated. This will need to be made available for import into Star Citizen.