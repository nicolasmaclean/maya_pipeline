#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:

:description:

"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-in
from dataclasses import dataclass
from enum import Enum
import json
import os

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CONTEXT --#


_context: 'PipeContext' = None


#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def _read_json(path: str):
    try:
        with open(os.path.expanduser(path), 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        return None
    except json.decoder.JSONDecodeError as e:
        return None

    return data


def get_pipe_context(path: str = None):
    # use default pipe context file path
    if not path:
        path = os.path.join(os.path.dirname(__file__), 'pipeline.json')

    if not os.path.isfile(path):
        raise FileNotFoundError(f'Unable to find the pipeline data file at {path}')

    # use the cached context, if still valid
    global _context
    last_modified = os.path.getmtime(path)
    if _context and last_modified == _context.last_modified:
        return _context

    # load context
    context_data = _read_json(path)
    if not context_data:
        raise RuntimeError(f'Unable to get pipeline data from {path}')
    _context = PipeContext.from_dict(context_data, last_modified)
    return _context


#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#


class Disk(Enum):
    WORK = 'work'
    STORE = 'store'
    CONFIG = 'config'


class ContextType(Enum):
    ASSET = 'asset'
    SET = 'set'
    SHOT = 'shot'


@dataclass
class DisciplineData:
    name: str
    name_nice: str
    context_type: ContextType


class Discipline(Enum):
    MODEL = DisciplineData('model', 'Modeling', ContextType.ASSET)
    SURFACE = DisciplineData('surface', 'Surfacing', ContextType.ASSET)
    RIG = DisciplineData('rig', 'Rigging', ContextType.ASSET)
    SET = DisciplineData('set', 'Set Dressing', ContextType.SET)
    LAY = DisciplineData('lay', 'Layout', ContextType.SHOT)
    ANI = DisciplineData('ani', 'Animation', ContextType.SHOT)
    LIT = DisciplineData('lit', 'Lighting', ContextType.SHOT)


class DCC(Enum):
    MAYA = 'maya'
    PAINTER = 'painter'
    UNREAL = 'unreal'


@dataclass
class DCCData(object):
    name: str
    path: str
    path_batch: str
    disciplines: set[Discipline]

    @classmethod
    def from_dict(cls, name, data, disciplines):
        return DCCData(
            name, data['path'],
            data['path_batch'] if 'path_batch' in data else None,
            disciplines
        )


@dataclass
class PipeContext(object):
    company: str
    version: str
    username: str
    home: str
    dccs: dict[DCC, DCCData]
    last_modified: float

    @classmethod
    def from_dict(cls, data: dict, last_modified: float):
        # parse dccs
        dccs = data['dccs']
        dccs = {
            DCC.MAYA: DCCData.from_dict(
                DCC.MAYA.value, dccs[DCC.MAYA.value],
                {Discipline.MODEL, Discipline.SURFACE, Discipline.RIG, Discipline.SET,
                 Discipline.LAY, Discipline.ANI, Discipline.LIT}),
            DCC.PAINTER: DCCData.from_dict(DCC.PAINTER.value, dccs[DCC.PAINTER.value],
                                           {Discipline.SURFACE}),
            DCC.UNREAL: DCCData.from_dict(DCC.UNREAL.value, dccs[DCC.UNREAL.value],
                                          {Discipline.SURFACE, Discipline.LIT}),
        }

        return PipeContext(
            data['company'], data['version'],
            data['user']['name'],
            f"{data['user']['home']}/{data['company']}",
            dccs, last_modified
        )


@dataclass
class AssetContext(object):
    dcc: DCC
    discipline: Discipline

    project: str
    group: str
    name: str

    def _get_asset_dir(self, disk: Disk):
        context = get_pipe_context()
        dcc = context.dccs[self.dcc]
        return f'{context.home}/{disk.value}/{self.project}/{self.discipline.value.name}/{self.group}/{self.name}/{dcc.name}'

    def get_asset_file(self, disk: Disk, name: str = None, ext: str = ''):
        if not name: name = self.name
        basename = '.'.join([name, ext])
        return f'{self._get_asset_dir(disk)}/{basename}'

    def get_version_dir(self, disk: Disk, version: int):
        if isinstance(version, int):
            version = f'{version:03}'
        return f'{self._get_asset_dir(disk)}/{version}'

    def get_version_file(self, disk: Disk, version: int = None, name: str = None, ext: str = ''):
        if not name: name = self.name
        basename = '.'.join([name, ext])
        return f'{self.get_version_dir(disk, version)}/{basename}'

    def get_active_file(self, disk: Disk, name: str = None, ext: str = ''):
        if not name: name = self.name
        basename = '.'.join([name, ext])
        return f'{self.get_version_dir(disk, "active")}/{basename}'

    def get_versions(self, disk: Disk):
        dir_versions = self._get_asset_dir(disk)
        if not os.path.isdir(dir_versions):
            return []
        versions = []
        for item in os.scandir(dir_versions):
            if item.is_file():
                continue
            try:
                version = int(item.name)
            except ValueError:
                continue
            versions.append((item.path, version))

        return versions

    def get_latest_version_dir(self, disk: Disk):
        versions = self.get_versions(disk)
        return None if not versions else versions[-1][0]

    def get_next_version_dir(self, disk: Disk):
        versions = self.get_versions(disk)
        if not versions:
            return self.get_version_dir(disk, 1)

        latest_version = versions[-1]
        next_version = latest_version[1] + 1
        return self.get_version_dir(disk, next_version)

    def get_next_version_file(self, disk: Disk, name: str = None, ext: str = ''):
        if not name:
            name = self.name

        versions = self.get_versions(disk)
        if not versions:
            return self.get_version_file(disk, 1, name, ext)

        latest_version = versions[-1]
        next_version = latest_version[0] + 1
        return self.get_version_file(disk, next_version, name, ext)

    def get_for_other_asset(self, group: str, name: str):
        return AssetContext(self.dcc, self.discipline, self.project, group, name)


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


def main():
    asset = AssetContext(DCC.MAYA, Discipline.MODEL, 'sunny', 'prop', 'z_nick')
    asset = asset.get_for_other_asset('prop', 'z_kellyn')
    print(asset.get_next_version_dir(Disk.WORK))
    # os.makedirs(asset.get_version_dir(Disk.WORK, 1))
    # os.makedirs(asset.get_version_dir(Disk.WORK, 2))


if __name__ == '__main__':
    main()
