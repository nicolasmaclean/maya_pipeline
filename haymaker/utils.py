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
import shutil

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
            if path_split[-2] == 'active':
                path_split = path_split[:-2] + path_split[-1:]

    # get new file name
    path_split.insert(-1, f'{version:04}')
    return '.'.join(path_split)


def get_version(path):
    path_split = path.split('.')
    if len(path_split) <= 1:
        return None

    if len(path_split) > 2:
        try:
            return int(path_split[-2])
        except ValueError:
            pass

    return None


def get_versions(path):
    path_split = path.split('.')
    if len(path_split) <= 1:
        log(f'path is wack!!!', level=Level.ERROR)
        return None

    if len(path_split) > 2:
        try:
            path_split = path_split[:-2] + path_split[-1:]
        except ValueError:
            pass
    path = '.'.join(path_split)

    versions = []
    for entry in os.scandir(os.path.dirname(path)):
        if not entry.is_file():
            continue

        version = get_version(entry.name)
        if version is not None:
            versions.append((entry.path, version))

    return versions


def get_latest_version(path):
    versions = get_versions(path)
    if not versions:
        return None

    latest = versions[0]
    for version in versions:
        if version[1] > latest[1]:
            latest = version
    return latest[0]


def get_active_path(path):
    path_split = path.split('.')
    if len(path_split) <= 1:
        log(f'path is wack!!!', level=Level.ERROR)
        return None

    if len(path_split) > 2:
        try:
            path_split = path_split[:-2] + path_split[-1:]
        except ValueError:
            pass

    # get new file name
    path_split.insert(-1, 'active')
    return '.'.join(path_split)


def version_file():
    path_file = cmds.file(q=True, sceneName=True)
    if not path_file:
        log(f'the scene needs to be saved before it can be versioned.', level=Level.ERROR)
        return None

    # get active and version path
    path_active = get_active_path(path_file)
    path_version = get_latest_version(path_file)
    if not path_version:
        path_version = path_active
    path_version = increment_version_path(path_version)

    # save active file
    cmds.file(rename=path_active)
    cmds.file(save=True)

    # slip in reference fixing
    foolproof_paths(notify=False)
    cmds.file(save=True)

    # save a version too
    shutil.copy(path_active, path_version)
    log(f'Saved active to {path_active} and version to {path_version}')
    return True
#endregion


def main():
    path_file = 'C:/Users/Nick/Box/Capstone_Uploads/05_Surfacing/SceneUploads/Warehouse.active.ma'
    path_active = get_active_path(path_file)
    path_version = get_latest_version(path_file)
    if not path_version:
        path_version = path_active
    path_version = increment_version_path(path_version)


if __name__ == '__main__':
    main()
