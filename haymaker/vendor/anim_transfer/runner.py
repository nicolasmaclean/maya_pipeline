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
import shutil

# Third Party
import maya.mel as mel

# Internal
from haymaker.log import log

# ----------------------------------------------------------------------------------------#
# --------------------------------------------------------------------------- FUNCTIONS --#


def open_gui():
    """
    Opens the mel gui from kfAnimTransfer.mel
    """
    # make sure the mel file is in the user's scripts folder
    # this allows us to directly call the mel procedure
    path_dst_mel = os.path.expanduser('~/Documents/maya/scripts/kfAnimTransfer.mel')
    if not os.path.isfile(path_dst_mel):
        dir_cur = os.path.dirname(__file__)
        path_src_mel = os.path.join(dir_cur, 'kfAnimTransfer.mel')
        shutil.copy(path_src_mel, path_dst_mel)

        path_dst_mel = path_dst_mel.replace('\\', '/')
        mel.eval(f'source "{path_dst_mel}";')

        log(f'Installed kfAnimTransfer.mel script to {path_dst_mel}')

    mel.eval('kfAnimTransfer();')
