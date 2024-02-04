#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Maya related utility functions

:applications:
    Maya
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
import os

# Third Party
from maya.api.OpenMaya import MSceneMessage
import maya.cmds as cmds
import maya
import maya.mel as mel

# Internal
from haymaker.log import log, Level
from haymaker import widgets

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def get_attr(node, attr):
    return cmds.getAttr(f'{node}.{attr}')


def set_attr(node, attr, value, t=None):
    if t:
        cmds.setAttr(f'{node}.{attr}', value, type=t)
    else:
        cmds.setAttr(f'{node}.{attr}', value)


def get_selected() -> [str]:
    return cmds.ls(selection=True)


def select(objs=None, all=None):
    if all:
        cmds.select(all=True)
        return
    cmds.select(objs)


#region Color Mode
def fix_selected_color_mode(notify=True):
    selection = get_selected()

    if not selection:
        confirm = widgets.UserConfirm(
            'Fix Texture Color Mode', 'You didn\'t select any objects. Do you want to '
            'try fixing the color mode on all objects in the scene?'
        )
        if not confirm.result:
            return None
        select(all=True)

    # use hypershade to select materials on the selected objects
    cmds.hyperShade("", smn=True)

    # look at the file nodes of the materials
    count = 0
    for material in get_selected():
        nodes = cmds.listConnections(material, type='file')
        if not nodes:
            continue
        for node in nodes:
            if fix_color_mode(node):
                count += 1

    select(selection)
    if notify:
        widgets.NotifyUser('Fixed Color Mode', f'Updated the color mode on {count} materials.')
    return count


def fix_color_mode(node):
    path_file = get_attr(node, 'fileTextureName')
    if not path_file:
        return None

    # detect texture type by file name
    name = os.path.basename(path_file)
    is_color = name[:name.find('.')].lower().endswith('_basecolor')

    # update the color mode
    if is_color:
        set_attr(node, 'colorSpace', 'sRGB', 'string')
        set_attr(node, 'alphaIsLuminance', False)
        log(f'Set {name}\'s color mode to BaseColor')
    else:
        set_attr(node, 'colorSpace', 'Raw', 'string')
        set_attr(node, 'alphaIsLuminance', True)
        log(f'Set {name}\'s color mode to Raw')

    return True
#endregion


#region File References
def reference_asset(path: str):
    """
    Creates (or duplicates) a reference to the provided file.
    WARNING: this may affect the current selection!
    """
    try:
        # duplicate reference, if this file is already reference
        node = cmds.file(path, q=True, referenceNode=True)
        cmds.select(node)
        mel.eval(f'duplicateReference 0 ""')
        log(f'Duplicated reference to {node}')
        return False
    except RuntimeError:
        # create reference
        cmds.file(path, reference=True)
        log(f'Created reference to {path}')
        return True


def foolproof_paths(notify=True):
    count = foolproof_user_references()
    count += foolproof_file_nodes()
    if notify:
        widgets.NotifyUser('Foolproof File Paths', f'Updated {count} file reference(s).')
    return count


_reference_create_callbacks = set()
def add_callback_to_reference_create(callback):
    global _reference_create_callbacks
    if callback in _reference_create_callbacks:
        return False

    _reference_create_callbacks.union([callback])
    MSceneMessage.addReferenceCallback(MSceneMessage.kAfterCreateReference, callback)
    return True


def get_foolproof_file_path(path):
    path_user = os.path.expanduser('~').replace('\\', '/')
    path_og = os.path.normpath(path).replace('\\', '/')

    path_new = os.path.normpath(path).replace('\\', '/')
    path_new = path.replace(path_user, '%USERPROFILE%')

    return (path_og, path_new)


def foolproof_user_references(*args):
    count = 0
    for ref in cmds.ls(type='reference'):
        if foolproof_user_reference(ref):
            count += 1
    log(f'Updated {count} file reference(s)')
    return count


def foolproof_user_reference(node):
    # ignore reference nodes without files
    try:
        path_ref_og = cmds.referenceQuery(node, filename=True, unresolvedName=True, withoutCopyNumber=True)
    except RuntimeError:
        return False

    # ignore, there is no reference
    if not path_ref_og:
        return False

    # remove the user path
    path_ref_og, path_ref = get_foolproof_file_path(path_ref_og)
    if path_ref_og == path_ref:
        return False

    # validate new path
    if not os.path.isfile(path_ref_og):
        log(f'unable to remove user from {node}\'s path: {path_ref_og} -> {path_ref}',
            level=Level.ERROR)
        return False

    # update the reference
    cmds.file(path_ref, loadReference=node)
    cmds.file(loadReference=node)
    log(f'updated {node} to a user path ({path_ref})')

    return True


def foolproof_file_nodes():
    count = 0
    for ref in cmds.ls(type='file'):
        if foolproof_file_node(ref):
            count += 1
    log(f'Updated {count} file node(s)')
    return count


def foolproof_file_node(node):
    attr = f'{node}.fileTextureName'
    path_og = cmds.getAttr(attr)

    # ignore, file node doesn't point anywhere yet
    if not path_og:
        return False

    # remove the user path
    path_og, path_new = get_foolproof_file_path(path_og)
    if path_og == path_new:
        return False

    # validate the new path
    if not os.path.isfile(path_og):
        log(f'unable to remove user from {node}\'s path: {path_og} -> {path_new}',
            level=Level.ERROR)
        return False

    # update the file node
    cmds.setAttr(attr, path_new, type='string')
    log(f'updated {node} to a user path ({path_new})')
    return True
#endregion


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


def main():
    pass


if __name__ == '__main__':
    main()
