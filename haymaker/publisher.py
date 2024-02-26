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

# Third Party
import maya.cmds as cmds
import maya.mel as mel

# Internal
from haymaker.enums import ResultType
from haymaker.maya import get_selected, get_active_file_path, select
from haymaker.widgets import NotifyUser
from haymaker.log import log, Level

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def publish_animation():
    # get objects to publish
    selected = get_selected()
    if not selected:
        NotifyUser(
            'Animation Publisher',
            'You must select the objects that you would like to publish',
            notify_type=None
        )
        return None

    # calculate publish directory
    path_active_file = get_active_file_path()
    name = os.path.basename(path_active_file).split('.')[0]
    dir_publish = os.path.expanduser(f'~/Box/Capstone_Uploads/07_Animation/Published/{name}')

    # make next version folder
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
    else:
        os.makedirs(dir_publish, exist_ok=True)
    version += 1
    dir_publish = os.path.join(dir_publish, f'{version:03}')
    os.makedirs(dir_publish, exist_ok=True)

    # get frame range
    start_frame = cmds.playbackOptions(q=True, animationStartTime=True)
    end_frame = cmds.playbackOptions(q=True, animationEndTime=True)

    # set fbx export settings
    mel.eval('FBXResetExport')
    mel.eval('FBXExportAnimationOnly -v 0')
    mel.eval('FBXExportBakeComplexAnimation -v 1')
    mel.eval('FBXExportBakeComplexStart -v %d' % start_frame)
    mel.eval('FBXExportBakeComplexEnd -v %d' % end_frame)
    mel.eval('FBXExportBakeResampleAnimation -v 0')
    mel.eval('FBXExportSplitAnimationIntoTakes -c')
    # mel.eval(f'FBXExportSplitAnimationIntoTakes - v \"tata\" {start_frame} {end_frame}')

    # Turn off the dialog box as we don't want to see it for every asset.
    mel.eval("FBXProperty Export|AdvOptGrp|UI|ShowWarningsManager -v 0")

    # publish!
    count = 0
    for obj in selected:
        # make sure the export object is a mesh
        if cmds.objectType(obj) != "transform":
            log(f'{obj} is not a transform. Not going to publish it.', Level.WARN)
            continue

        # select the specific object, then export selection
        # also remove the namespace from the object, if present
        select(obj)
        obj = obj.split(':')[0]
        path_publish = os.path.join(dir_publish, obj)
        cmds.file(path_publish, force=True, options="v=0;", typ="FBX export", es=True)
        count += 1

    # restore selection
    select(selected)

    # publish was successful
    NotifyUser(
        'Animation Publisher',
        f'{count} asset(s) successfully published.'
    )
    return True
