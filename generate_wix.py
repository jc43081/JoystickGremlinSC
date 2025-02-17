"""Generate the wix XML file for the setup generation."""

import argparse
import os
import uuid
import sys
import pickle
from xml.dom import minidom
from xml.etree import ElementTree

def generate_file_list(root_folder):
    """Returns a list of file paths in the given folder.

    :param root_folder the base folder to traverse
    :return list of file paths relative to the root folder
    """
    file_list = []
    for root, _, files in os.walk(root_folder):
        for fname in files:
            file_list.append(
                    os.path.relpath(os.path.join(root, fname), root_folder)
            )
    return file_list


def generate_folder_list(root_folder):
    """Returns a list of folder paths in the given folder.

    :param root_folder the base folder to traverse
    :return list of folder paths relative to the root folder
    """
    folder_list = []
    for root, dirs, _ in os.walk(root_folder):
        for folder in dirs:
            folder_list.append(
                os.path.relpath(os.path.join(root, folder), root_folder)
            )
    return folder_list


def sanitize_path(path):
    """Formats the paths in an acceptable way for wix.

    :param path path to sanitize
    :return sanitized file path
    """
    return path.replace("\\", "__").replace("-", "_").replace("@", "_").replace("+", "_")


def create_data_for_file(path):
    """Creates the entries required to create the file's XML entries.

    :param path the file path for which to create the entries
    :return dictionary containing required information
    """
    return {
        "component_guid": uuid.uuid4(),
        "component_id": f"component_{sanitize_path(path)}",
        "file_id": f"file_{sanitize_path(path)}",
        "file_source": path
    }


def create_node(tag, data):
    """Creates a new XML node.

    :param tag the tag of the XML node
    :param data the attributes of the node
    :return newly created XML node
    """
    node = ElementTree.Element(tag)
    for key, value in data.items():
        node.set(key, str(value))
    return node


def create_folder_structure(folder_list):
    """Creates the basic XML directory structure.

    :param folder_list the list of folders present
    :return dictionary with folder nodes
    """
    structure = {}

    # Create the basic structure for where to place the actual files
    structure["root"] = create_node(
        "StandardDirectory",
        {"Id": "AppDataFolder"}
    )
    structure["h2ik"] = create_node(
        "Directory",
        {"Id": "H2ik", "Name": "H2ik"}
    )
    structure["jg"] = create_node(
        "Directory",
        {"Id": "INSTALLDIR", "Name": "Joystick Gremlin SC"}
    )
    structure["root"].append(structure["h2ik"])
    structure["h2ik"].append(structure["jg"])

    # Component to remove the H2ik folder
    node = create_node(
        "Component",
        {
            "Guid": "cec7a9a7-d686-4355-8d9d-e1d211d3edb8",
            "Id": "H2ikProgramFilesFolder"
        }
    )
    node.append(create_node(
        "RemoveFolder",
        {"Id": "RemoveH2iKFolder", "On": "uninstall"})
    )
    structure["h2ik"].append(node)

    # Create the folder structure for the Joystick Gremlin install
    for folder in folder_list:
        dirs = folder.split("\\")
        for i in range(len(dirs)):
            path = sanitize_path("__".join(dirs[:i+1]))
            if path not in structure:
                structure[path] = create_node(
                    "Directory",
                    {"Id": sanitize_path(path), "Name": dirs[i]}
                )
                if i > 0:
                    parent_path = sanitize_path("__".join(dirs[:i]))
                    structure[parent_path].append(structure[path])

        # Link top level folders to the install folder
        if len(dirs) == 1:
            dirName = sanitize_path(dirs[0])
            structure["jg"].append(structure[dirName])

    return structure


def add_file_nodes(structure, data):
    """Creates component and file nodes in the appropriate directories.

    :param structure dictionary of directory nodes
    :param data the file node data
    """
    for path, entry in data.items():
        # Create component and file nodes
        c_node = ElementTree.Element("Component")
        c_node.set("Id", entry["component_id"])
        c_node.set("Guid", str(entry["component_guid"]))

        f_node = ElementTree.Element("File")
        f_node.set("Id", entry["file_id"])
        f_node.set("KeyPath", "yes")
        f_node.set(
            "Source",
            os.path.join("joystick_gremlin", entry["file_source"])
        )

        c_node.append(f_node)

        # Attach component node to the proper directory node
        parent = sanitize_path(os.path.dirname(path))
        if len(parent) == 0:
            parent = "jg"
        structure[parent].append(c_node)


def create_feature(data):
    """Creates the feature node containing all components.

    :param data file structure data
    :return feature node
    """
    node = create_node(
            "Feature",
            {
                "Id": "Complete",
                "Level": 1,
                "Title": "Joystick Gremlin SC",
                "Description": "The main program",
                "Display": "expand",
                "ConfigurableDirectory": "INSTALLDIR"
            })
    node.append(create_node(
        "ComponentRef", {"Id": "ProgramMenuDir"}
    ))
    node.append(create_node(
        "ComponentRef", {"Id": "H2ikProgramFilesFolder"}
    ))
    for entry in data.values():
        node.append(create_node(
            "ComponentRef",
            {"Id": entry["component_id"]}
        ))
    return node


def create_document():
    """Creates the basic XML document layout.

    :return top level document
    """
    doc = ElementTree.Element("Wix")
    doc.set("xmlns", "http://wixtoolset.org/schemas/v4/wxs")
    doc.set("xmlns:ui", "http://wixtoolset.org/schemas/v4/wxs/ui")

    # https://www.uuidgenerator.net/
    pkg = create_node(
        "Package",
        {
            "Name": "Joystick Gremlin SC",
            "Manufacturer": "H2IK",
            # "Id": "a0a7fc85-8651-4b57-b7ee-a7f718857939", # 4.0.0
            # "Id": "447529e9-4f78-4baf-b51c-21db602a5f7b", # 4.0.1
            # "Id": "510CBEE4-3947-11E6-8BA5-2DD7CD7856CC", # 5.0.0
            # "Id": "a02bac10-af70-41c2-b109-34e80eb54902", # 6.0.0
            # "Id": "278cbeb5-9da1-4f82-8775-fd6f78f92283", # 7.0.0
            # "Id": "a84b71f4-90d4-44f6-a3d8-df7f47b60090", # 7.1.0
            # "Id": "0ac91685-2681-4b0c-9d22-3a25edf21325", # 8.0.0
            # "Id": "0be39e58-8099-4cd9-8efd-60735249c907", # 8.1.0
            # "Id": "769bf0f8-ba2c-45fb-bc92-d521ed81e721", # 9.0.0
            # "Id": "83417e4c-5acc-49fe-9938-0624a681e6e5", # 9.1.0
            # "Id": "ce0c7c9f-8bcc-4676-a96b-da602968e85e", # 9.2.0
            # "Id": "bec63861-eeae-4f75-bb01-3a76cab1c319", # 10.0.0
            # "Id": "5598cb71-2825-4a78-8f4b-682aefd14323", # 11.0.0
            # "Id": "290a3110-0745-48d6-93d2-d954cb584b6f", # 12.0.0
            # "Id": "6019660b-26bd-430b-9b95-ca6a55201060",  # 13.0.0
            # "Id": "0dad4221-c8cf-4424-8dcd-3886274e89ef", # 13.1.0
            #"Id": "6472cca8-d352-4186-8a98-ca6ba33d083c", # 13.40.6ex
            #"Id": "7cdb8375-66a1-4114-be79-b17027e8c0df", # 13.40.7ex
            #"Id": "739095a7-19cc-4154-ac9c-c51f5f516527", # 13.40.8ex
            "ProductCode": "ecf47554-75cb-40a8-ab8a-938b7ac63e99", # 13.40.14-sc.1
            "UpgradeCode": "1f5d614b-6cec-47d8-90e3-40f7e7458f7a",
            "Language": "1033",
            "Codepage": "1252",
            "Version": version,
            "InstallerVersion": "100"
        })
    
    # also change version number in joystick_gremlin.py line 60 APPLICATION_VERSION
    
    mug = create_node("MajorUpgrade",
        {
            "AllowSameVersionUpgrades": "yes",
            "DowngradeErrorMessage":
                "Cannot directly downgrade, uninstall current version first."
        }
    )
    summary = create_node(
        "SummaryInformation",
        {
            "Keywords": "Installer",
            "Description": "Joystick Gremlin SC R{}".format(version) + " Installer",
            "Manufacturer": "H2IK"
        }
    )

    # Package needs to be added before media
    pkg.append(summary)
    pkg.append(mug)
    pkg.append(create_node(
        "Media",
        {
            "Id": "1",
            "Cabinet": "joystick_gremlin.cab",
            "EmbedCab": "yes"
        }
    ))

    # Add the icon to the software center
    pkg.append(create_node(
        "Property",
        {"Id": "ARPPRODUCTICON", "Value": "icon.ico"}
    ))
    # Remvoe the repair option from the installer
    pkg.append(create_node(
        "Property",
        {"Id": "ARPNOREPAIR", "Value": "yes", "Secure": "yes"}
    ))

    doc.append(pkg)

    return doc


def create_ui_node(parent):
    """Creates the UI definitions.

    :param parent the parent node to which to attach the UI nodes
    """
    ui = create_node("UI", {})
    ui.append(create_node("ui:WixUI", {"Id": "WixUI_InstallDir", "InstallDirectory": "INSTALLDIR"}))
    ui.append(create_node("UIRef", {"Id": "WixUI_ErrorProgressText"}))

    # Skip the license screen
    n1 = create_node(
        "Publish",
        {
            "Dialog": "WelcomeDlg",
            "Control": "Next",
            "Event": "NewDialog",
            "Value": "InstallDirDlg",
            "Order": "2"
        }
    )
    n2 = create_node(
        "Publish",
        {
            "Dialog": "InstallDirDlg",
            "Control": "Back",
            "Event": "NewDialog",
            "Value": "WelcomeDlg",
            "Order": "2"
        }
    )
    ui.append(n1)
    ui.append(n2)

    parent.append(ui)


def create_shortcuts(package):
    """Creates program shortcut nodes.

    :param doc the main document
    :param root the root directory node
    """

    # Find the executable node and add shortcut entries
    for node in package.iter("File"):
        if node.get("Id") == "file_joystick_gremlin.exe":
            node.append(create_node(
                "Shortcut",
                {
                    "Id": "startmenu_joystick_gremlin",
                    "Directory": "ProgramMenuDir",
                    "Name": "Joystick Gremlin SC",
                    "WorkingDirectory": "INSTALLDIR",
                    "Advertise": "yes",
                    "Icon": "icon.ico"
                }
            ))
            node.append(create_node(
                "Shortcut",
                {
                    "Id": "desktop_joystick_gremlin",
                    "Directory": "DesktopFolder",
                    "Name": "Joystick Gremlin SC",
                    "WorkingDirectory": "INSTALLDIR",
                    "Advertise": "yes",
                    "Icon": "icon.ico"
                }
            ))

    # Create folder names used for the shortcuts
    n1 = create_node(
        "StandardDirectory",
        {"Id": "ProgramMenuFolder"}
    )
    n2 = create_node(
        "Directory",
        {"Id": "ProgramMenuDir", "Name": "Joystick Gremlin SC"}
    )
    n3 = create_node(
        "Component",
        {"Id": "ProgramMenuDir", "Guid": "a9736055-0450-47f3-96a5-e38b2ab7218d"}
    )
    n3.append(create_node(
        "RemoveFolder",
        {"Id": "ProgramMenuDir", "On": "uninstall"}
    ))
    n3.append(create_node(
        "RegistryValue",
        {
            "Root": "HKCU",
            "Key": "Software\\H2ik\\Joystick Gremlin SC",
            "Type": "string",
            "Value": "",
            "KeyPath": "yes"
        }
    ))
    n2.append(n3)
    n1.append(n2)
    package.append(n1)

    package.append(create_node(
        "StandardDirectory",
        {"Id": "DesktopFolder"}
    ))

    # Create the used icon
    package.append(create_node(
        "Icon",
        {"Id": "icon.ico", "SourceFile": "joystick_gremlin\\gfx\\icon.ico"}
    ))


def write_xml(node, fname):
    """Saves the XML document to the given file.

    :param node node of the XML document
    :param fname the file to store the XML document in
    """

    # ugly_xml = ElementTree.tostring(node, encoding="unicode")
    # dom_xml = minidom.parseString(ugly_xml)
    # with open(fname, "w") as out:
    #     out.write(dom_xml.toprettyxml(indent="    "))

    
    tree = ElementTree.ElementTree(node)
    ElementTree.indent(tree)
    tree.write(fname, xml_declaration=True, encoding="utf-8")

def main():
    # Command line arguments
    parser = argparse.ArgumentParser("Generate WIX component data")
    parser.add_argument(
        "--folder",
        default="dist/joystick_gremlin",
        help="Folder to parse"
    )
    parser.add_argument(
        "--version",
        default="13.x.x",
        help="Version to use"
    )    
    args = parser.parse_args()

    global version 
    version = args.version

    # Attempt to load existing file data
    data = {}
    if os.path.exists("wix_data.p"):
        data = pickle.load(open("wix_data.p", "rb"))

    # Create file list and update data for new entries
    file_list = generate_file_list(args.folder)
    for path in file_list:
        if path not in data:
            data[path] = create_data_for_file(path)
    paths_to_delete = []
    for path in data.keys():
        if path not in file_list:
            paths_to_delete.append(path)
    for path in paths_to_delete:
        del data[path]

    pickle.dump(data, open("wix_data.p", "wb"))

    # Create document and file structure
    folder_list = generate_folder_list(args.folder)
    structure = create_folder_structure(folder_list)
    add_file_nodes(structure, data)

    # Assemble the complete XML document
    document = create_document()
    package = document.find("Package")
    package.append(create_feature(data))
    package.append(structure["root"])
    create_shortcuts(package)
    create_ui_node(package)

    # Save the XML document
    write_xml(document, "joystick_gremlin.wxs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
