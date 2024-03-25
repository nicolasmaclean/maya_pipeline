#!/usr/bin/env python
# SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Collection of classes and functions to publish an asset or shot.
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
import os.path
import shutil
import tempfile

# Third Party
import maya.cmds as cmds

# Internal
from haymaker.enums import ResultType
from haymaker.maya import get_selected, get_active_file_path
from haymaker.widgets import NotifyUser
from haymaker.log import log
from haymaker.maya import MayabatchExecuter

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def publish_animation_in_background():
    """
    Starts a mayabatch to publish the animation.
    """
    # don't bother starting if nothing is selected
    selected = get_selected()
    if not selected:
        NotifyUser(
            'Animation Publisher',
            'You must select the objects that you would like to publish',
            notify_type=None
        )
        return None

    # make a copy of the current animation file that will be the publish file
    file_copy, path_copy = tempfile.mkstemp(suffix='.ma')
    os.close(file_copy)
    path_active_file = get_active_file_path()
    shutil.copy(path_active_file, path_copy)

    # make next version folder
    name = os.path.basename(path_active_file).split('.')[0]
    dir_publish = os.path.expanduser(f'~/Box/Capstone_Uploads/07_Animation/Published/{name}')
    version = 0
    if os.path.isdir(dir_publish):
        with os.scandir(dir_publish) as it:
            for entry in it:
                if not entry.is_dir():
                    continue
                try:
                    version_entry = int(entry.name)
                    if version_entry > version:
                        version = version_entry
                except ValueError:
                    continue
    version += 1
    dir_publish = os.path.join(dir_publish, f'{version:03}')
    os.makedirs(dir_publish, exist_ok=True)

    # create a status file
    with open(os.path.join(dir_publish, 'log.txt'), 'w') as file:
        file.write(f'Preparing publish for...\n'
                   f'\t{",".join(selected)}\n')

        # process the file and publish it
        path_final = os.path.join(dir_publish, f'{name}.ma').replace('\\', '/')
        py_cmd = (f'from haymaker.publisher import _publish_animation; '
                  f'_publish_animation("{selected}", "{path_final}")')
        exe = MayabatchExecuter('Publish - Animation')
        process = exe.run(path_maya_file=path_copy, command=py_cmd)

        # check if process started
        if process:
            file.write(f'Started publishing...\n'
                       f'\t{py_cmd}\n')
            NotifyUser(
                title='Publish - Animation',
                message='Animation publish has successfully started in the background.'
            )
        else:
            file.write(f'Failed to start background process\n'
                       f'\t{py_cmd}\n')
            NotifyUser(
                title='Publish - Animation',
                message='Animation publish failed to start.'
            )

    return bool(process)


def _publish_animation(objs, path_publish):
    """
    Publishes this file for animation. Strips file to objs and bakes references.

    :param objs: objects to preserve
    :type: [str]

    :param path_publish: final path the active maya file should be saved to
    :type: str
    """
    with open(os.path.join(os.path.dirname(path_publish), 'log.txt'), 'a') as file:
        # unpack stringified list
        if isinstance(objs, str):
            objs = objs[1:-1].replace('\'', '').split(',')
            file.write(f'Unpacked stringified list\n')

        # include all user-cameras in the publish
        cameras = [cmds.listRelatives(c, p=True)[0]
                   for c in cmds.ls(type='camera')
                   if not cmds.camera(c, q=True, sc=True)]
        objs += cameras

        # delete everything but objects and their dependencies
        # an additional pass is done to remove file references too
        cmds.select(all=True)
        cmds.select(objs, deselect=True)
        cmds.select(objs, deselect=True, allDependencyNodes=True)
        cmds.delete()
        file.write('Stripped objects from scene\n')

        # import references (and sub-references)
        references = set()
        for obj in objs:
            try:
                node = cmds.referenceQuery(obj, referenceNode=True, topReference=True)
            except RuntimeError:
                pass
            references.add(cmds.referenceQuery(node, filename=True))

        path_references: set[str] = set(cmds.file(q=True, reference=True))
        while len(path_references) > 0:
            path_reference = path_references.pop()

            # remove non-dependent and unloaded references
            nondependent = path_reference not in references
            unloaded = not cmds.referenceQuery(path_reference, isLoaded=True)
            if nondependent or unloaded:
                cmds.file(path_reference, removeReference=True)
                log(f'Removed reference to {path_reference}')
                continue

            # ignore unloaded references
            if not cmds.referenceQuery(path_reference, isLoaded=True):
                continue

            # import reference
            cmds.file(path_reference, importReference=True)
            log(f'Import reference to {path_reference}')

            # make sure to collect sub-references
            path_references = path_references.union(cmds.file(q=True, reference=True))
        file.write('Imported references\n')

        # move the file to the final publish location
        path_temp = get_active_file_path()
        cmds.file(rename=path_publish)
        cmds.file(save=True)
        os.remove(path_temp)
        file.write(f'Moved publish file to {path_publish}\n')
