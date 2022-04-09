# Author: Joseph McGurkin
# Description:
#   This script creates a BOM from the active component. 
#   If no component is active, the root component is used. 
#   Output is a markdown file with images in an images folder.
# Notes:
#   Yes, there are solutions which simply iterate through the root component's all occurrences.
#   However, if an assembly has child linked assemblies and those children have grandchildren links,
#   the linked grandchild cannot be isolated for an image.

from inspect import getfile
import adsk.core, adsk.fusion, adsk.cam, traceback, urllib, time

def getFolder(ui, title):
    folderDialog = ui.createFolderDialog()
    folderDialog.title = title
    dialogResult = folderDialog.showDialog()
    if dialogResult == adsk.core.DialogResults.DialogOK:
        return folderDialog.folder + "\\"
    return None

def hideAll(design, ui):
    bulbDialog = None
    if design.rootComponent.allOccurrences.count > 50:
        bulbDialog = ui.createProgressDialog()
        bulbDialog.cancelButtonText = 'Cancel'
        bulbDialog.isBackgroundTranslucent = False
        bulbDialog.isCancelButtonShown = True
        bulbDialog.show('Step 1 of 2, hiding everything...', '%p percent complete, component %v of %m', 0, design.rootComponent.allOccurrences.count, 1)
    for occ in design.rootComponent.allOccurrences:
        occ.isLightBulbOn = False
        if bulbDialog:
            bulbDialog.progressValue = bulbDialog.progressValue + 1
            if bulbDialog.wasCancelled: return
    if bulbDialog is not None:
        bulbDialog.hide()
        bulbDialog = None

def sortPartNumber(k):
    return k['partNumber']

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
                viewPort.saveAsImageFile(filePath, 100, 100)
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
        ui  = app.userInterface
        activeProduct = app.activeProduct
        design = adsk.fusion.Design.cast(activeProduct)
        if not design:
            ui.messageBox('Please switch to the Design workspace.', 'Scratch')
            return

        viewPort = app.activeViewport
        startComp = design.activeComponent
        turnedOffGrid = False

        rootFolder = getFolder(ui, "Selcect a folder for the BOM")
        imagesFolder = rootFolder + "images" + "\\"

        # If grid is on, temporarily turn off
        cmdDef = ui.commandDefinitions.itemById('ViewLayoutGridCommand')
        listCntrlDef = adsk.core.ListControlDefinition.cast(cmdDef.controlDefinition)
        layoutGridItem = listCntrlDef.listItems.item(0)
        if layoutGridItem.isSelected:
            layoutGridItem.isSelected = False
            turnedOffGrid = True

        hideAll(design, ui)

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
            startComp.isBodiesFolderLightBulbOn = False

        occDialog = None
        if startComp.allOccurrences.count > 1:
            occDialog = ui.createProgressDialog()
            occDialog.cancelButtonText = 'Cancel'
            occDialog.isBackgroundTranslucent = False
            occDialog.isCancelButtonShown = True
            occDialog.show('Step 2 of 2, exporting BOM...', '%p percent complete, component %v of %m', 0, startComp.allOccurrences.count, 1)

        start = time.time()

        processOccs(startComp.occurrences.asList, imagesFolder, viewPort, occDialog, bomList)

        end = time.time()
        processElapsed = end-start
        
        # Get image of start assembly
        for occ in startComp.allOccurrences:
            occ.isLightBulbOn = True
        startComp.isBodiesFolderLightBulbOn = True
        viewPort.fit()
        startPartNumber = startComp.partNumber + " Assembly"
        startImageFileName = startPartNumber + '.png'
        startImagePath = urllib.parse.quote("images/" + startImageFileName)
        startFilePath = "{}{}.png".format(imagesFolder, startPartNumber)
        viewPort.saveAsImageFile(startFilePath, 200, 200)

        bomList.sort(key=sortPartNumber)
        initialFilename = startComp.partNumber + " BOM"
        mdText = "# " + initialFilename + "\n"
        mdText += "![](" + startImagePath + ")\n"
        mdText += "|Image|Name|Number|Quantity|Description|\n|-|-|-|-|-|"
        for bomItem in bomList:
            mdText = mdText + "\n|![](" + bomItem['imagePath'] + ")|" + bomItem['partName'] +  "|" + bomItem['partNumber'] +  "|" + str(bomItem['instances']) + "|" + bomItem['description'] + "|"
        with open(rootFolder + "\\" + urllib.parse.quote(initialFilename) + ".md", "w") as outputFile:
            outputFile.writelines(mdText)

        if occDialog:
            occDialog.hide()

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
