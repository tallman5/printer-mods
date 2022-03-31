#Author-Joseph McGurkin
#Description-Exports BOM to CSV

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        product = app.activeProduct

        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('No active design', 'Generate BOM')
            return
            
        # ui.messageBox('Select a destination to output the Bill of Materials to...')
        
        # Get all occurrences in the root component of the active design
        root = design.rootComponent
        occs = root.allOccurrences
        
        # Gather information about each unique component
        bom = []
        for occ in occs:
            comp = occ.component
            jj = 0
            for bomI in bom:
                if bomI['component'] == comp:
                    # Increment the instance count of the existing row.
                    bomI['instances'] += 1
                    break
                jj += 1

            if jj == len(bom):
                # Gather any BOM worthy values from the component
                volume = 0
                bodies = comp.bRepBodies
                for bodyK in bodies:
                    if bodyK.isSolid:
                        volume += bodyK.volume
                
                # Add this component to the BOM
                if comp.occurrences.count <= 1:
                    bom.append({
                        'component': comp,
                        'partNumber': comp.partNumber,
                        'description': comp.description,
                        'instances': 1,
                        'volume': volume,
                        'childOccurrences': occ.childOccurrences.count,
                        'occurrences': comp.occurrences.count
                    })

        fileDialog = ui.createFileDialog()
        fileDialog.isMultiSelectEnabled = False
        fileDialog.title = "Set the file to save the BOM to..."
        fileDialog.filter = 'Text files (*.csv)'
        fileDialog.filterIndex = 0
        dialogResult = fileDialog.showSave()
            
        if dialogResult == adsk.core.DialogResults.DialogOK:
            filename = fileDialog.filename
        else:
            return
        
        result = "Part Number,Description,Quantity\n"
        for item in bom:
            result = result + "\"" + item['partNumber'] +  "\",\"" + item['description'] + "\",\"" + str(item['instances']) + "\"\n"
        
        with open(filename, "w") as outputFile:
            outputFile.writelines(result)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
