# Author: Joseph McGurkin
# Description: Parts pasted using "Past New" end up with a (index) at the end of the name.
#       This script finds the indexed ones and updates the part numbers.
#       After which accurate BOM counts can be generated.

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        activeProduct = app.activeProduct
        design = adsk.fusion.Design.cast(activeProduct)
        if not design:
            ui.messageBox('Please switch to the Design workspace.', 'Udpate Part Numbers')
            return
        
        allComponents = design.allComponents

        progressDialog = ui.createProgressDialog()
        progressDialog.cancelButtonText = 'Cancel'
        progressDialog.isBackgroundTranslucent = False
        progressDialog.isCancelButtonShown = True
        progressDialog.show('Updating part numbers...', '%p percent complete, component %v of %m', 0, allComponents.count, 1)

        updateCounter = 0
        for comp in allComponents:
            partNumber = comp.partNumber
            if partNumber.endswith(")"):
                reversedText = "".join(reversed(partNumber))
                openParenIndex = reversedText.find('( ')
                if openParenIndex > -1:
                    partNumber = partNumber[0:(len(partNumber)-openParenIndex-2)]
                    comp.partNumber = partNumber
                    updateCounter += 1
            progressDialog.progressValue += 1
            if progressDialog.wasCancelled:
                break

        progressDialog.hide()
        message = 'Finshed, udpated {} part numbers.'.format(updateCounter)
        ui.messageBox(message)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
