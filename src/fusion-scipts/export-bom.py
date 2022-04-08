# Author: Joseph McGurkin
# Description:
#   This script creates a BOM from the active component. 
#   If no component is active, the root component is used. 
#   Output is a markdown file with images in an images folder.
# Notes:
#   Yes, there are solutions which simply iterate through the root component's all occurrences.
#   However, if an assembly has child linked assemblies and those children have grandchildren links,
#   the linked grandchild cannot be isolated for an image.

import adsk.core, adsk.fusion, adsk.cam, traceback, urllib, time

def sortPartNumber(k):
    return k['partNumber']

def sortComponentPartNumber(k):
    return k['component'].partNumber

def processOccs(occs, imagesFolder, viewPort, progressDialog, bomList):
    for occ in occs:
        occ.isLightBulbOn = True
        if occ.component.bRepBodies.count > 0:
            partNumber = occ.component.partNumber
            itemFound = False
            for bomItem in bomList:
                if bomItem['partNumber'] == partNumber:
                    bomItem['instances'] += 1
                    itemFound = True
                    break

            if not itemFound:
                viewPort.fit()
                imageFileName = partNumber + '.png'
                imagePath = urllib.parse.quote("images/" + imageFileName)
                filePath = "{}{}.png".format(imagesFolder, partNumber)
                viewPort.saveAsImageFile(filePath, 200, 200)
                bomList.append({
                    'imagePath': imagePath,
                    'partName': occ.name,
                    'partNumber': partNumber,
                    'instances': 1,
                    'material': '',
                    'description': occ.component.description,
                })

            for body in occ.component.bRepBodies:
                body.isLightBulbOn = False

                
        processOccs(occ.childOccurrences, imagesFolder, viewPort, progressDialog, bomList)
        for body in occ.component.bRepBodies:
            body.isLightBulbOn = True
        occ.isLightBulbOn = False

        if progressDialog:
            progressDialog.progressValue = progressDialog.progressValue + 1
            if progressDialog.wasCancelled: return

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        viewPort = app.activeViewport
        ui  = app.userInterface
        activeProduct = app.activeProduct
        design = adsk.fusion.Design.cast(activeProduct)

        if not design:
            ui.messageBox('Please switch to the Design workspace.', 'Scratch')
            return

        folderDialog = ui.createFolderDialog()
        folderDialog.title = "Selcect a folder for the BOM"
        dialogResult = folderDialog.showDialog()
        if dialogResult == adsk.core.DialogResults.DialogOK:
            rootFolder = folderDialog.folder + "\\"
            imagesFolder = rootFolder + "images" + "\\"
        else:
            return

        # If grid is on, temporarily turn off
        turnedOffGrid = False
        cmdDef = ui.commandDefinitions.itemById('ViewLayoutGridCommand')
        listCntrlDef = adsk.core.ListControlDefinition.cast(cmdDef.controlDefinition)
        layoutGridItem = listCntrlDef.listItems.item(0)
        if layoutGridItem.isSelected:
            layoutGridItem.isSelected = False
            turnedOffGrid = True

        startComp = design.activeComponent

        progressDialog = ui.createProgressDialog()
        progressDialog.cancelButtonText = 'Cancel'
        progressDialog.isBackgroundTranslucent = False
        progressDialog.isCancelButtonShown = True
        progressDialog.show('Step 1 of 2, hiding everything...', '%p percent complete, component %v of %m', 0, design.rootComponent.allOccurrences.count, 1)

        for occ in design.rootComponent.allOccurrences:
            occ.isLightBulbOn = False
            progressDialog.progressValue = progressDialog.progressValue + 1
            if progressDialog.wasCancelled: return
        progressDialog.hide()

        # If not root, need to light up each between the root and the selcected item
        if design.rootComponent != design.activeComponent:
            parentCtx = design.activeOccurrence
            while parentCtx is not None:
                parentCtx.isLightBulbOn = True
                parentCtx = parentCtx.assemblyContext

        bomList = []
        
        # If the selected item has bodies and occurrences, need to get the bodies before working all occurrences
        if startComp.bRepBodies.count > 0:
            viewPort.fit()
            partNumber = startComp.partNumber
            imageFileName = partNumber + '.png'
            imagePath = urllib.parse.quote("images/" + imageFileName)
            filePath = "{}{}.png".format(imagesFolder, partNumber)
            viewPort.saveAsImageFile(filePath, 200, 200)
            bomList.append({
                'imagePath': imagePath,
                'partName': startComp.name,
                'partNumber': partNumber,
                'instances': 1,
                'material': '',
                'description': startComp.description,
            })

        progressDialog = None
        if startComp.allOccurrences.count > 1:
            progressDialog = ui.createProgressDialog()
            progressDialog.cancelButtonText = 'Cancel'
            progressDialog.isBackgroundTranslucent = False
            progressDialog.isCancelButtonShown = True
            progressDialog.show('Step 2 of 2, exporting BOM...', '%p percent complete, component %v of %m', 0, startComp.allOccurrences.count, 1)

        start = time.time()
        processOccs(startComp.occurrences.asList, imagesFolder, viewPort, progressDialog, bomList)

        end = time.time()
        processElapsed = end-start

        bomList.sort(key=sortPartNumber)
        initialFilename = startComp.partNumber + " BOM"
        mdText = "# " + initialFilename + "\n|Image|Name|Number|Quantity|Description|\n|-|-|-|-|-|"
        for bomItem in bomList:
            mdText = mdText + "\n|![](" + bomItem['imagePath'] + ")|" + bomItem['partName'] +  "|" + bomItem['partNumber'] +  "|" + str(bomItem['instances']) + "|" + bomItem['description'] + "|"
        with open(rootFolder + "\\" + urllib.parse.quote(initialFilename) + ".md", "w") as outputFile:
            outputFile.writelines(mdText)

        if progressDialog:
            progressDialog.hide()

        if turnedOffGrid == True:
            layoutGridItem.isSelected = True

        sels = ui.activeSelections
        sels.clear()
        sels.add(design.rootComponent)
        app.executeTextCommand('Commands.Start ShowAllComponentsCmd')
        app.executeTextCommand('Commands.Start ShowAllBodiesCmd')
        sels.clear()
        viewPort.fit()

        end = time.time()
        totalElapsed = end-start

        message = 'Finished\n'
        message += 'Process time: ' + time.strftime("%Hh %Mm %Ss", time.gmtime(processElapsed)) + '\n'
        message += 'Total time: ' + time.strftime("%Hh %Mm %Ss", time.gmtime(totalElapsed))
        ui.messageBox(message)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
