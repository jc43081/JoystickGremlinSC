import json
import pathlib
from xml.dom import minidom
from xml.etree import ElementTree


version="4.6.x"
profile_name = "JG_StarCitizenMapping_" + version.replace('.','-')
actionmap_template = "layout_template.xml"
controls_mapping = "../controls_mappings/StarCitizenControlsMapping-" + version + ".json"
output_file = "layout_" + profile_name + "_exported.xml"
controls_list = {}
actionmaps = {}

def map_axis(axis_number):
    match axis_number:
        case 1:
            return "x"
        case 2:
            return "y"
        case 3:
            return "z"
        case 4:
            return "rotx"
        case 5:
            return "roty"
        case 6:
            return "rotz"
        case 7:
            return "slider1"
        case 8:
            return "slider2"
        case _:
            return ""

def map_vjoy(vjoy_number):
    match vjoy_number:
        case 1:
            return "js1"
        case 2:
            return "js2"
        case 3:
            return "js3"
        case 4:
            return "js4"
        case 5:
            return "js5"
        case 6:
            return "js6"
        case _:
            return ""


def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem          

# Read in the ActionMap Template
try:
    actionmaps = ElementTree.parse(actionmap_template)
except:
    print("Unable to read in ActionMap Tempate. Make sure the template is valid XML and file is available.")
    exit


# Read in the Mappings JSON
try:
    controls_list = json.loads(pathlib.Path(controls_mapping).read_text(encoding="UTF-8"))
except:
    print("Unable to read in Controls Mapping. Make sure the Controls Mappings is valid JSON and file is available.")
    exit

# Update the profile name to match
actionmaps._root.attrib['profileName'] = profile_name
ui_header = actionmaps.find("CustomisationUIHeader")
ui_header.attrib["label"] = profile_name

# cycle through Control List and update the ActionMap Template
for category in controls_list:
    for control in category["values"]:
        disabled = False if control.get("disabled") == None else control["disabled"]
        if disabled:
            pass
        else:
            control_actionmap = control["actionmap"]
            control_action = control["action"]

            print("Processing -> Control Name: " + control["name"] + " | ActionMap - " + control_actionmap + "; Action - " + control_action)

            # Find the actionmap and if not found, create it
            actionmap_name = "actionmap[@name='" + control_actionmap + "']"
            actionmap = actionmaps.findall(actionmap_name)
            actionmap_element = None
            if actionmap == []:
                actionmap_element = ElementTree.SubElement(actionmaps.getroot(), "actionmap", {"name": control_actionmap })
            elif len(actionmap) > 0:
                actionmap_element = actionmap[0]
            else:
                print("ActionMap incorrect. Multiple instances of '" + control_actionmap +'"')
                exit

            action = ElementTree.SubElement(actionmap_element, "action", { "name": control_action})
            binding = ""
            if control["type"] == "button":
                binding = map_vjoy(control["vjoy"]) + "_button" + str(control["button"])
            else:
                binding = map_vjoy(control["vjoy"]) + "_" + map_axis(control["axis"])
            rebind = ElementTree.SubElement(action, "rebind", {"input": binding})

indent(actionmaps.getroot())
actionmaps.write(output_file)



