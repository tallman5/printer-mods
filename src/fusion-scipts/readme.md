# Fusion Scripts
The scripts in this folder can be added in Fusion 360 as an add-in.

## Scripts

### Update Part Numbers
Components which are the same, but not linked will have a *(index)* at the end of the name. This script will update the component's part number to the same as the name, however without the *(index)* at the end. This does not *link* components. N.B. If you have intentionally added the parenthesis at the end, they will be removed from the component's part number.

### Attribute Editor
Components have a collection of attributes in the form of Group Name, Name and Value. This script allows the attributes of the selected component to be edited. A use case is described in the Export BOM below.

### Export BOM
Generates a BOM from the selected component. Output is a markdown file with a table and images of each component.

If an assembly has a child component with children (grandchildren), only the bottom level components (ones with no children) are exported. For example, a 3D printer with a Raspberry Pi may be modeled as:
1. Printer Assembly
   1. Steppers
   1. ...
   1. Raspberry Pi
      1. PCB
      1. RJ45 Connector
      1. Molex USB Connector
   1. ...

In sample above, only the PCB, RJ45 and Molex components are exported.

Export BOM can export the Raspberry Pi as a single assembly with all of its children instead of exporting only all of the children individually. Use the Attribute Editor above to customize how the BOM is generated. In the Pi sample, the Raspberry Pi component needs an *isSingleAssembly* attribute as *True*. During an export, the script will see the single assembly attribute, export 1 Raspberry Pi and will image the Pi with all of its child components. All of the attributes are simple strings with no type checking. So, watch the spelling. The Export BOM script will traverse the entire tree of components and look for special instructions in each component's attributes. The following table lists the attributes currently in use by the Export BOM script.

|Group Name|Name|Value|Description|
|-|-|-|-|
|exportBom|ignore|True|Do not export this component and all of its children|
|exportBom|isSingleAssembly|True|Export the component including all of its children as a single BOM item, all children will not be exported individually|

## Setup
### Prerequisites
1. Fusion 360
1. Visual Studio Code
1. Latest version of Python

### To Use
1. Start Fusion 360
1. In the menu, select UTILITIES -> ADD-INS
1. In the Scripts and Add-Ins dialog, click Create
1. In the Create New Script or Add-In dialog:
   1. Create a New: Script
   1. Programming Language: Python
   1. Script or Add-In Name: *script name*
   1. Fill in other properties if desired
   1. Click Create
1. Back in the Scripts and Add-Ins dialog, click Debug in the Run dropdown
1. Visual Studio Code should open
1. Paste the text from the script's specific Python file
1. Press F5 to run it