#Author: Joseph McGurkin
#Description: This script creates a BOM from the active component. If no component is active, the root component is used. Output is a CSV and a markdown file with images in an images folder.

import adsk.core, adsk.fusion, adsk.cam, traceback, urllib

def sortPartNumber(k):
    return k['partNumber']

def run(context):
    ui = None

    # If components where copied and pasted as new, they'll have (index) at the end on the part number
    # Set parsePartNumbers to True to parse out the (index)
    parsePartNumbers = True

    try:
        app = adsk.core.Application.get()
        viewPort = app.activeViewport
        ui  = app.userInterface

        activeProduct = app.activeProduct
        design = adsk.fusion.Design.cast(activeProduct)
        if not design:
            ui.messageBox('Please switch to the Design workspace.', 'Scratch')
            return

        rootComponent = design.rootComponent
        initialFilename = rootComponent.partNumber + " BOM"
        startOccurrences = allOccurrences = rootComponent.allOccurrences

        for occ in allOccurrences:
            if occ.isActive:
                startComponent = occ.component
                startOccurrences = startComponent.allOccurrences
                initialFilename = startComponent.partNumber + " BOM"
                break

        folderDialog = ui.createFolderDialog()
        folderDialog.title = "Selcect a folder for the BOM"
        dialogResult = folderDialog.showDialog()
        if dialogResult == adsk.core.DialogResults.DialogOK:
            rootFolder = folderDialog.folder
            imagesFolder = rootFolder + "\\" + "images"
        else:
            return

        progressDialog = ui.createProgressDialog()
        progressDialog.cancelButtonText = 'Cancel'
        progressDialog.isBackgroundTranslucent = False
        progressDialog.isCancelButtonShown = True
        progressDialog.show('Exporting BOM...', '%p percent complete, component %v of %m', 0, startOccurrences.count, 1)

        bomList = []

        if startOccurrences.count > 0:
            for occurrence in startOccurrences:
                component = occurrence.component

                if component.bRepBodies.count > 0:
                    existingBomItem = None

                    partNumber = component.partNumber
                    if parsePartNumbers == True:
                        if partNumber.endswith(")"):
                            reversedText = "".join(reversed(partNumber))
                            openParenIndex = reversedText.find('( ')
                            if openParenIndex > -1:
                                partNumber = partNumber[0:(len(partNumber)-openParenIndex-2)]

                    for bomItem in bomList:
                        if bomItem['partNumber'] == partNumber:
                            bomItem['instances'] += 1
                            existingBomItem = bomItem
                            break

                    if existingBomItem is None:
                        # Get the occurrence from root all occurrences
                        # For some reason, the viewport would zoom if using
                        # the start component's all occurrences
                        occ = None
                        for allOcc in allOccurrences:
                            if allOcc.component == component:
                                occ = allOcc
                                break

                        occ.activate()
                        occ.isIsolated = True

                        # Occurrences with bodies and child occurences are BOM'd as a full assembly
                        # Need a way to hide child components and show only bodies
                        # for childOcc in occ.childOccurrences:
                        #     childOcc.isVisible = False

                        imageFileName = partNumber + '.png'
                        imagePath = urllib.parse.quote("images/" + imageFileName)
                        viewPort.fit()
                        viewPort.saveAsImageFile(imagesFolder + "\\" + imageFileName, 100, 100)

                        bomList.append({
                            'component': component,
                            'imagePath': imagePath,
                            'partNumber': partNumber,
                            'instances': 1,
                            'material': '',
                            'description': component.description,
                        })

                        occurrence.isIsolated = False

                    if progressDialog.wasCancelled:
                        break
                
                progressDialog.progressValue = progressDialog.progressValue + 1

        bomList.sort(key=sortPartNumber)

        mdText = "# " + initialFilename + "\n|Image|Part Number|Quantity|Description|\n|-|-|-|-|\n"
        csvText = "Part Number,Quantity,Description\n"
        for bomItem in bomList:
            mdText = mdText + "|![](" + bomItem['imagePath'] + ")|" + bomItem['partNumber'] +  "|" + str(bomItem['instances']) + "|" + bomItem['description'] +  "|\n"
            csvText = csvText + "\"" + bomItem['partNumber'] +  "\",\"" + str(bomItem['instances']) + "\",\"" + bomItem['description'] +  "\"\n"
        
        with open(rootFolder + "\\" + initialFilename + ".md", "w") as outputFile:
            outputFile.writelines(mdText)
        
        with open(rootFolder + "\\" + initialFilename + ".csv", "w") as outputFile:
            outputFile.writelines(csvText)

        progressDialog.hide()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
