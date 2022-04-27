#Author: Joseph McGurkin
#Description: Edits the attributes of the selected component

import adsk.core, adsk.fusion, traceback

_app = None
_ui  = None
_rowNumber = 0
_attrs = None
_activeComponent = None

# Global set of event handlers to keep them referenced for the duration of the command
_handlers = []

# Adds a new row to the table.
def addRowToTable(tableInput, groupName, attrName, attrValue):
    global _rowNumber
    # Get the CommandInputs object associated with the parent command.
    cmdInputs = adsk.core.CommandInputs.cast(tableInput.commandInputs)

    groupNameInput =  cmdInputs.addStringValueInput('TableInput_string{}'.format(_rowNumber), 'String', groupName)
    nameInput =  cmdInputs.addStringValueInput('TableInput_string{}'.format(_rowNumber), 'String', attrName)
    valueInput =  cmdInputs.addStringValueInput('TableInput_string{}'.format(_rowNumber), 'String', attrValue)

    row = tableInput.rowCount
    tableInput.addCommandInput(groupNameInput, row, 0)
    tableInput.addCommandInput(nameInput, row, 1)
    tableInput.addCommandInput(valueInput, row, 2)

    # Increment a counter used to make each row unique.
    _rowNumber = _rowNumber + 1

# Event handler that reacts to any changes the user makes to any of the command inputs.
class AeCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input

            tableInput = inputs.itemById('attrEditorTable')
            if cmdInput.id == 'tableAdd':
                addRowToTable(tableInput, "", "", "")
            elif cmdInput.id == 'tableDelete':
                if tableInput.selectedRow == -1:
                    _ui.messageBox('Select one row to delete.')
                else:
                    tableInput.deleteRow(tableInput.selectedRow)
          
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler that reacts to when the command is destroyed. This terminates the script.            
class AeCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            if args.terminationReason == 1:
                # User clicked OK
                # Rather than try to match, just clear all attributes
                # and add ones from the table
                attrs = _activeComponent.attributes
                for i in reversed(range(0, attrs.count)):
                    attr = attrs.item(i)
                    attr.deleteMe()

                inputs = args.command.commandInputs
                table = inputs.itemById('attrEditorTable')
                for row in range(0, table.rowCount):
                    g = str(table.getInputAtPosition(row,0).value)
                    n = table.getInputAtPosition(row,1).value
                    v = table.getInputAtPosition(row,2).value
                    if len(g) > 0 and len(n) > 0 and len(v) > 0:
                        attrs.add(g, n, v)

            adsk.terminate()
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class AeCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)

            # Connect to the command destroyed event.
            onDestroy = AeCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)

            # Connect to the input changed event.           
            onInputChanged = AeCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)    

            # Get the CommandInputs collection associated with the command.
            inputs = cmd.commandInputs
            
            message = 'Enter new attributes for the selected component. Fill in Group Name, Attribute Name and Attribute Value. All fields are required.'
            inputs.addTextBoxCommandInput('fullWidth_textBox', '', message, 5, True)            

            # Create table input
            tableInput = inputs.addTableCommandInput('attrEditorTable', 'Attributes', 3, '1:1:1')
            for attr in _attrs:
                addRowToTable(tableInput, attr.groupName, attr.name, attr.value)

            # Add inputs into the table.            
            addButtonInput = inputs.addBoolValueInput('tableAdd', 'Add', False, '', True)
            tableInput.addToolbarCommandInput(addButtonInput)
            deleteButtonInput = inputs.addBoolValueInput('tableDelete', 'Delete', False, '', True)
            tableInput.addToolbarCommandInput(deleteButtonInput)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    try:
        global _app, _ui, _attrs, _activeComponent
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        product = _app.activeProduct

        design = adsk.fusion.Design.cast(product)
        if not design:
            _ui.messageBox('Please change to MODEL workspace and try again.')
            return

        _activeComponent = design.activeComponent
        _attrs = _activeComponent.attributes

        # Get the existing command definition or create it if it doesn't already exist.
        cmdDef = _ui.commandDefinitions.itemById('attributeEditor')
        if not cmdDef:
            cmdDef = _ui.commandDefinitions.addButtonDefinition('attributeEditor', 'Attribute Editor', 'Edit component attributes')

        # Connect to the command created event.
        onCommandCreated = AeCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Execute the command definition.
        cmdDef.execute()

        # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))