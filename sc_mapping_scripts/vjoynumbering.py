import json
import pathlib

controls_mapping = "..//controls_mappings//StarCitizenControlsMapping-4.6.x-OnFoot.json"
controls_list = {}


# Read in the Mappings JSON
try:
    controls_list = json.loads(pathlib.Path(controls_mapping).read_text(encoding="UTF-8"))
except:
    print("Unable to read in Controls Mapping. Make sure the Controls Mappings is valid JSON and file is available.")

# Initialize vjoy variables 
current_button_vjoy = 1
current_button = 1
current_axis_vjoy = 1
current_axis = 1

vjoy_button_max = 128

for category in controls_list:
    for control in category["values"]:
        disabled = False if control.get("disabled") == None else control["disabled"]
        if disabled:
            if control["type"] == "button":
                control["button"] = 0
            else:
                control["axis"] = 0
            control["vjoy"] = 0
        else:
            if control["type"] == "button":
                control["button"] = current_button
                control["vjoy"] = current_button_vjoy
                
                current_button = current_button + 1
                if current_button > vjoy_button_max:
                    current_button = 1
                    current_button_vjoy = current_button_vjoy + 1
                    vjoy_button_max = vjoy_button_max - 1
            
            if control["type"] == "axis":
                control["axis"] = current_axis
                control["vjoy"] = current_axis_vjoy

                current_axis = current_axis + 1
                if current_axis > 8:
                    current_axis = 1
                    current_axis_vjoy = current_axis_vjoy + 1

max_vjoys = current_button_vjoy
if current_axis_vjoy > current_button_vjoy:
    max_vjoys = current_axis_vjoy

print("Needed Vjoys: ", max_vjoys)
print("Vjoy needed for Buttons: ", current_button_vjoy)
print("Last Button Mapped: ", current_button-1)
print("Vjoy needed for Axis: ", current_axis_vjoy)
print("Last Axis Mapped: ", current_axis-1)

with open(controls_mapping+".mapped", 'w') as json_file:
    json.dump(controls_list, json_file, indent=4)

#print(controls_list)