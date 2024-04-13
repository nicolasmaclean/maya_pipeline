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
    create_animation(menu)


def _add_item(parent, label, command):
    log_injection = f'from haymaker.log import log; log("Menu - {label}"); '
    cmds.menuItem(parent=parent, label=label, command=log_injection + command)


def create_general(parent):
    _add_item(parent, 'Version Current File',
              'from haymaker.utils import version_file; version_file()')
    _add_item(parent, 'Foolproof File paths',
              'from haymaker.maya import foolproof_paths; foolproof_paths()')
    _add_item(parent, 'Delete Unknown Nodes',
              'from haymaker.maya import delete_unknown_nodes; delete_unknown_nodes()')
    _add_item(parent, 'Submit Log',
              'from haymaker.log import submit_log; submit_log()')


def create_surfacing(parent):
    cmds.menuItem(parent=parent, divider=True, dividerLabel='Surfacing')

    _add_item(
        parent, 'Fix Texture Color Spaces', 'from haymaker.maya import '
        'fix_selected_color_mode; fix_selected_color_mode()'
    )
    _add_item(
        parent, 'Export Material Assignments', 'from haymaker.guis.material_assignment '
        'import save_material_assignments; save_material_assignments()'
    )
    _add_item(
        parent, 'Import Material Assignments', 'from haymaker.guis.material_assignment '
        'import load_material_assignments; load_material_assignments()'
    )


def create_animation(parent):
    cmds.menuItem(parent=parent, divider=True, dividerLabel='Animation')

    _add_item(
        parent, 'Transfer Animation',
        'from haymaker.vendor.anim_transfer.runner import open_gui; open_gui()'
    )
    _add_item(
        parent, 'Publish Animation',
        'from haymaker.publisher import publish_animation; publish_animation()'
    )


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


create_menu()
# hook_startup()
