
# create Scripts shelf if it does not exist
if not cmds.shelfLayout('Scripts', exists=True):
    mel.eval('addNewShelfTab "Scripts"')

# add FK IK tool button to shelf
cmds.shelfButton(
    parent='Scripts',
    label='FK IK Tool',
    annotation='Open FK IK Rig Tool Window',
    imageOverlayLabel='FKIK',
    image='commandButton.png',
    command='''
import sys
import importlib
