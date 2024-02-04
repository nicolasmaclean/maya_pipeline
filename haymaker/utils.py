#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick

:synopsis:
    General utilities for other code or users
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-in
import json
import os

# 3rd Party
try:
    from maya import cmds
    from haymaker.maya import foolproof_paths
except ImportError:
    print('WARNING: Cannot import maya.cmds in this environment')

# Internal
from haymaker.log import log, Level

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def get_or_default(d: dict, key, default):
    try:
        return d[key]
    except KeyError:
        return default


#region Files
def read_json(path: str, verbose: bool = True):
    try:
        with open(os.path.expanduser(path), 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        if verbose:
            log(f'Could not find json file at {path}', level=Level.ERROR)
        return None
    except json.decoder.JSONDecodeError as e:
        if verbose:
            log(f'Unable to parse json file at {path} :: {e}', level=Level.ERROR)
        return None

    return data


def normalize_path(path: str):
    return os.path.normpath(path).replace('\\', '/')


def normalize_user_path(path: str):
    user_path = normalize_path(os.path.expanduser('~'))
    return normalize_path(path).replace(user_path, '~')
#endregion


#region Versioning
def increment_version_path(path, delta=1):
    path_split = path.split('.')
    version = 1
    if len(path_split) <= 1:
        log(f'path is wack!!!', level=Level.ERROR)
        return None

    if len(path_split) > 2:
        try:
            version = int(path_split[-2]) + delta
            path_split = path_split[:-2] + path_split[-1:]
        except ValueError:
            pass

    # get new file name
    path_split.insert(-1, f'{version:04}')
    return '.'.join(path_split)


def get_version_path(path, version):
    path_split = path.split('.')
    if len(path_split) <= 1:
        log(f'path is wack!!!', level=Level.ERROR)
        return None

    if len(path_split) < 2:
        try:
            path_split = path_split[:-2] + path_split[-1:]
        except ValueError:
            pass

    # get new file name
    path_split.insert(-1, f'{version:04}')
    path_new = '.'.join(path_split)


def version_file():
    path_file = cmds.file(q=True, sceneName=True)
    if not path_file:
        log(f'the scene needs to be saved before it can be versioned.', level=Level.ERROR)
        return None

    # get current version number
    path_new = increment_version_path(path_file)
    if path_new is None:
        return None

    # save to new file
    cmds.file(rename=path_new)
    cmds.file(save=True)
    log(f'Saved new version to {path_new}')

    # slip in reference fixing
    foolproof_paths(notify=False)
    cmds.file(save=True)

    return True
#endregion
