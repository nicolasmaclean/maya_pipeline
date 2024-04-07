#!/usr/bin/env python
# SETMODE 777

# ----------------------------------------------------------------------------------------#
# ------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:

:description:

:applications:
    None

:see_also:
"""


# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------- IMPORTS --#

# Built-In
import os

# Third Party

# Internal
from haymaker.maya import get_selected, SurfacingUtils
import haymaker.widgets as widgets
from haymaker.log import log, Level
from haymaker.utils import write_json, read_json

# External

# ----------------------------------------------------------------------------------------#
# --------------------------------------------------------------------------- FUNCTIONS --#


def save_material_assignments():
    # validate object selection
    selection = get_selected()
    if len(selection) != 1:
        widgets.NotifyUser(
            'Export Material Assignments',
            message='Please select a SINGLE root object to save materials from.',
            notify_type=False
        )
        return None

    # get file path to save to
    path_output = widgets.get_save_file(
        filter='Data files (*.json)',
        caption='Save the currently selected object\'s material assignments'
    )
    if not path_output:
        log('Please select a file to save the material assignment to.', level=Level.WARN)
        return None

    # get material assignments
    data = SurfacingUtils.get_material_assignments(selection[0])
    if not data:
        widgets.NotifyUser(
            'Export Material Assignments',
            message='It seems there was an error collecting the material assignments to'
                    'export. Check the log for errors.',
            notify_type=False
        )
        return None

    # save material assignments to disk
    os.makedirs(os.path.dirname(path_output), exist_ok=True)
    result = write_json(path_output, data)
    if not result:
        widgets.NotifyUser(
            'Export Material Assignments',
            message='It seems there was an error saving the material assignments to disk.',
            notify_type=False
        )

    return result


def load_material_assignments():
    # validate object selection
    selection = get_selected()
    if len(selection) != 1:
        widgets.NotifyUser(
            'Import Material Assignments',
            message='Please select a SINGLE root object to assign materials to.',
            notify_type=False
        )
        return None

    # get file path to load from
    path_data = widgets.get_open_file(
        filter='Data files (*.json)',
        caption='Apply materials from data file'
    )
    if not path_data:
        log('Please select a file to load the material assignments from.', level=Level.WARN)
        return None

    # read material assignments from disk
    assignments = read_json(path_data)
    if not assignments:
        widgets.NotifyUser(
            'Import Material Assignments',
            message='It seems there was an error reading the material assignments from disk.',
            notify_type=False
        )
        return None

    result = SurfacingUtils.set_material_assignments(selection[0], assignments)
    if not result:
        widgets.NotifyUser(
            'Import Material Assignments',
            message='It seems there was an error applying the materials.',
            notify_type=False
        )

    return result
