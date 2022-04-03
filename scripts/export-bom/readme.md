# Export BOM
Export BOM is an add-in script for Fusion 360 which exports a BOM to a CSV and to an MD with imagees. If there is an active component in the model browser, a BOM will be created from the active component and all child components. If there is no active component, the root component will be used.

## Prerequisites
1. Fusion 360
1. Visual Studio Code
1. Latest version of Python

## To Use
1. Start Fusion 360
1. In the menu, select UTILITIES -> ADD-INS
1. In the Scripts and Add-Ins dialog, click Create
1. In the Create New Script or Add-In dialog:
   1. Create a New: Script
   1. Programming Language: Python
   1. Script or Add-In Name: export-bom
   1. Fill in other properties if desired
   1. Click Create
1. Back in the Scripts and Add-Ins dialog, click Debug in the Run dropdown
1. Visual Stuio Code should open
1. Paste the text from the expoort-bom.py file
1. Run it!