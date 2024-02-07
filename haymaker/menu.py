#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Creates a menu in your toolbar with Haymaker's tools.
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Third Party
import maya.cmds as cmds
import maya.mel as mel

# Internal
from haymaker.log import log
from haymaker.maya import add_callback_to_reference_create, foolproof_user_references

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- GLOBALS --#

MENU_NAME = 'Haymaker'

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def hook_startup():
    add_callback_to_reference_create(foolproof_user_references)


def create_menu():
    """
    Creates (will remove previous menu if already present) menu in toolbar for Haymaker.
    """
    # If the menu already exists, delete it and all its contents
    menus = cmds.lsUI(menus=True)
    for item in menus:
        try:
            menu_label = cmds.menu(item, label=1, query=True)
        except RuntimeError:
            continue
        if menu_label == MENU_NAME:
            cmds.menu(item, deleteAllItems=True, edit=True)
            cmds.deleteUI(item)

    # Make the menu
    gMainWindow = mel.eval('$temp1=$gMainWindow')
    menu = cmds.menu(parent=gMainWindow, tearOff=True, label=MENU_NAME)

    # Populate menu
    create_general(menu)
    create_surfacing(menu)


def _add_item(parent, label, command):
    log_injection = f'from haymaker.log import log; log("Menu - {label}"); '
    cmds.menuItem(parent=parent, label=label, command=log_injection + command)


def create_general(parent):
    _add_item(parent, 'Version Current File',
              'from haymaker.utils import version_file; version_file()')
    _add_item(parent, 'Foolproof File paths',
              'from haymaker.maya import foolproof_paths; foolproof_paths()')
    _add_item(parent, 'Submit Log',
              'from haymaker.log import submit_log; submit_log()')


def create_surfacing(parent):
    cmds.menuItem(parent=parent, divider=True, dividerLabel='Surfacing')

    _add_item(
        parent, 'Fix Texture Color Spaces', 'from haymaker.maya import '
        'fix_selected_color_mode; fix_selected_color_mode()'
    )


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


create_menu()
hook_startup()