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
from dataclasses import dataclass
import os
from tempfile import NamedTemporaryFile

# Third Party
# noinspection PyUnresolvedReferences
from maya.api.OpenMaya import MSceneMessage
# noinspection PyUnresolvedReferences
import maya.cmds as cmds
# noinspection PyUnresolvedReferences
import maya.mel as mel

# Internal
from haymaker.app_exe import notify_system, Process, AppExecuter
from haymaker.log import log, Level
import haymaker.widgets as widgets

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


def get_active_file_path() -> str:
    return cmds.file(q=True, sceneName=True)


def delete_unknown_nodes():
    """
    This function removes all unknown nodes from the maya scene.

    :return: Nodes removed, otherwise None
    :type: list
    """
    nodes = cmds.ls(type='unknown')
    cmds.delete(nodes)
    if nodes:
        print('UNKNOWN NODES DELETED')
        for node in nodes:
            print(f'\t{node}')
        return nodes

    print('No unknown nodes to delete')
    return None


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
    path_new = path_new.replace(path_user, '%USERPROFILE%')

    return path_og, path_new


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


def fix_other_users_paths(path_user):
    for node in cmds.ls(type='file'):
        path = cmds.getAttr(f'{node}.fileTextureName')
        path_new = path.replace(path_user, '%USERPROFILE%')
        if path != path_new:
            cmds.setAttr(f'{node}.fileTextureName', path_new, type='string')

#endregion


#region App Executer
@dataclass
class MayaProcess(Process):
    """
    QProcess wrapper that overrides the subprocess errors with Maya's python errors.
    """
    stdout: int = None
    stderr: int = None

    path_errors: str = None

    def _get_result(self):
        result, errors = super()._get_result()

        # override errors with output file
        # this is because errors in python code executed in the mayabatch will not be
        # returned as errors of the subprocess, so we have to manually extract them
        with open(self.path_errors, 'r') as file:
            errors += file.read()
        os.remove(self.path_errors)

        return result, errors


class MayabatchExecuter(AppExecuter):
    """
    Easily run mayabatch in the background and setup notifications.

    exec = MayabatchExecuter('Example Task')
    exec.run(path_maya_file=path_file, func=('utils', 'func'))
    """
    NAME_EXE = 'mayabatch.exe'

    def __init__(self, name=None, name_exe=None, path_exe=None):
        super().__init__(name, name_exe, path_exe)
        self._path_errors = None

    @classmethod
    def _get_exe_path(cls, name_exe: str) -> str:
        path = super()._get_exe_path(name_exe)

        # try hard-coded path to mayabatch, if the PATH variable has not been injected
        # this should only be the case when this py interpreter is not Maya's embedded one
        return path if path else 'C:/Program Files/Autodesk/Maya2023/bin/mayabatch.exe'

    def _create_process(self, args, on_finish) -> Process:
        return MayaProcess(self.NAME, self.path_exe, args, on_finish,
                           path_errors=self._path_errors)

    def run(self, on_finish=notify_system, path_maya_file: str = None, command: str = None,
            func = None, *args, **kwargs):
        """
        Opens mayabatch.exe and runs the provided python code. One of command, path_py,
        or func must be provided.

        :param on_finish: callback to perform upon execution completion
        :type: func(ProcessResult) -> None

        :param path_maya_file: (optional) maya file to work with
        :type: str

        :param command: string of python code to run. should be 1 line (with ;'s)
        :type: str

        :param func: a python function to run
        :type: (absolute path to py module, name of function)

        :param args:
        :param kwargs:

        :return: the resulting subprocess
        :type: Popen
        """
        # if given a maya file, validate it
        if path_maya_file and not os.path.isfile(path_maya_file):
            return None
        path_maya_file = path_maya_file.replace('\\', '/')

        # prepare python code to run
        if func:
            command = f'from {func[0]} import {func[1]}; {func[1]}()'
        if not command:
            return None

        # make a file to write errors to
        # python errors in mayabatch are sent to stdout, so we need to do some trickery
        # to extract errors from it
        file_errors = NamedTemporaryFile(delete=False)
        self._path_errors = path_errors = file_errors.name
        file_errors.close()

        # write python command to a temp file for mayabatch to run
        #   this will help prevent issues caused by running arbitrary py code in mel
        #   inject cleanup code and environment setup
        with NamedTemporaryFile('w', delete=False) as file_py:
            path_py = file_py.name
            file_py.write('\n'.join([
                f'try:',
                f'    {command}',
                f'except Exception as e:',
                f'    import traceback',
                f'    with open(r\'{path_errors}\', \'w\') as file:',
                f'        file.write(traceback.format_exc())',
                f'finally:',
                f'    import os',
                f'    os.remove(r\'{path_py}\')',
            ]))

        # run mayabatch!
        path_py = path_py.replace('\\', '\\\\')
        mel = f'python(\"exec(open(r\'{path_py}\', \'r\').read())\")'
        if path_maya_file:
            process, started = super().run(on_finish=on_finish, file=path_maya_file,
                                           command=mel, *args, *kwargs)
        else:
            process, started = super().run(on_finish=on_finish, command=mel, *args, *kwargs)

        # manually clean up temp files, failed processes probably won't be able to do this
        if not started:
            if os.path.isfile(path_py):
                os.remove(path_py)
            if os.path.isfile(path_errors):
                os.remove(path_errors)
            return None

        return process, started
#endregion


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


def main():
    pass


if __name__ == '__main__':
    main()
