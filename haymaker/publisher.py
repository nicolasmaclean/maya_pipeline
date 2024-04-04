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
from math import ceil
import os.path
import shutil
import tempfile

# Third Party
import maya.cmds as cmds

# Internal
from haymaker.maya import get_active_file_path
from haymaker.widgets import NotifyUser
from haymaker.log import log, Level
from haymaker.maya import MayabatchExecuter

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def split_into_batches(items: list, max_batches):
    """
    Generator that evenly splits the list of items into the maximum amount of batches.

    :return: generator of sub-lists
    """
    # keep it simple, we have enough batches to give each item its own batch
    if len(items) <= max_batches:
        for item in items:
            yield [item]
        return

    # try to evenly distribute across the batches
    # take a naive approach. create batches that are too big till we have trimmed
    # the size of the list, so we can do small batches
    batch_size = len(items) / max_batches
    big_batch = ceil(batch_size)
    small_batch = int(batch_size)
    i = 0
    batches_left = max_batches
    while batches_left:
        use_small_batches = (batches_left * small_batch) >= len(items) - i
        batch_size = small_batch if use_small_batches else big_batch
        yield items[i:i+batch_size]
        batches_left -= 1
        i += batch_size


def publish_animations(paths, max_batches=3):
    """
    Publishes animation files in the background. Batches them to prevent overwhelming your
    computer.

    :param paths: files to publish
    :type: [str]

    :param max_batches: max number of batches to publish files in
    :type: int

    :return: ([success files that were published], [files that failed to published])
    :type: ([str], [str])
    """
    success = []
    fail = []
    # for path in split_into_batches(paths, max_batches):
    for path in paths:
        if not path:
            log(f'Please provide valid paths to publish: "{path}"', Level.WARN)
        elif publish_animation(path):
            success.append(path)
        else:
            fail.append(path)
    return success, fail


def publish_animation(path_work=None):
    """
    Publishes the provided work file (or uses the currently open file) in the background.
    It will create a copy of this file that has pruned to only the necessary objects.

    :return: success
    """
    # we were not given a file to publish because it's currently open
    # make the current maya scene is ready to publish
    if not path_work:
        cmds.file(save=True)
        path_work = get_active_file_path()
        if not path_work:
            NotifyUser(
                title='Publish - Animation', notify_type=None,
                message='You must save this file before you can publish it.'
            )
            return None

    # make a copy of the current animation file that will be the publish file
    file_copy, path_copy = tempfile.mkstemp(suffix='.ma')
    os.close(file_copy)
    shutil.copy(path_work, path_copy)

    # make next version folder
    name = os.path.basename(path_work).split('.')[0]
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
        file.write(f'Preparing publish for...\n')

        # start the publish process
        path_final = os.path.join(dir_publish, f'{name}.ma').replace('\\', '/')
        py_cmd = (f'from haymaker.publisher import _bg_publish_animation; '
                  f'_bg_publish_animation("{path_final}")')
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


def _bg_publish_animation(path_publish):
    """
    Publishes this file for animation. Strips file to objs and bakes references.

    :param path_publish: final path the active maya file should be saved to
    :type: str
    """
    with open(os.path.join(os.path.dirname(path_publish), 'log.txt'), 'a') as file:
        # include all user-cameras in the publish
        cameras = [cmds.listRelatives(c, p=True)[0]
                   for c in cmds.ls(type='camera')
                   if not cmds.camera(c, q=True, sc=True)]

        # delete all non-references and cameras
        cmds.select(cmds.ls(type='transform'))
        cmds.select(cameras, deselect=True)
        cmds.delete()
        file.write('Stripped objects from scene\n')

        # remove unnecessary references and import all the other ones
        path_rigging = os.path.expanduser('~/Box/Capstone_Uploads/04_Rigging').replace('\\', '/')
        for node in cmds.ls(references=True):
            try:
                path = cmds.referenceQuery(node, filename=True)
            except RuntimeError:
                # the reference node doesn't reference a file, just ignore it
                # I have no idea how this happens 🤷‍
                # ideally, we delete the node, but I can't figure out how
                continue

            # if this is a nested reference, just ignore it
            is_child = cmds.referenceQuery(node, referenceNode=True, parent=True)
            if is_child:
                continue

            loaded = cmds.referenceQuery(path, isLoaded=True)
            is_rig = path.startswith(path_rigging)
            has_cam = False  # TODO:

            # case 1: a loaded reference is a rigged character or has a camera we might
            # be using. Import it.
            if loaded and (is_rig or has_cam):
                cmds.file(path, importReference=True)
                log(f'Import reference to {path}')
                continue

            # case 2: reference is unloaded, is a set, or is anything else. Delete it.
            cmds.file(path, removeReference=True)
        file.write('Filtered references\n')

        # move the file to the final publish location
        path_temp = get_active_file_path()
        cmds.file(rename=path_publish)
        cmds.file(save=True)
        os.remove(path_temp)
        file.write(f'Moved publish file to {path_publish}\n')
