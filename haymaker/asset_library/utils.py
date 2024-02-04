#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Utilities to upload, reference, and manage files in the library.

:applications:
    Maya
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
from dataclasses import dataclass, asdict
import json
import os.path
import shutil
from uuid import uuid4

# Internal
from haymaker.log import log, Level
from haymaker.utils import normalize_user_path

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#


@dataclass
class Config(object):
    dir_root: str
    catalog_name: str
    dir_thumbnails: str

    @staticmethod
    def from_dict(data: dict):
        dir_root = get_or_default(data, 'root', None)
        name = get_or_default(data, 'catalog_name', None)
        dir_thumbnails = get_or_default(data, 'dir_thumbnails', None)
        return Config(dir_root, name, dir_thumbnails)

    @staticmethod
    def load(path: str = None):
        # default to ./formulas.json
        if not path or not os.path.isfile(path):
            path = os.path.dirname(__file__)
            path = os.path.join(path, 'formulas.json')

        config_data = read_json(path)
        if not config_data:
            raise RuntimeError('Unable to read a formulas.json.')

        log(f'Read config from {path}')
        return Config.from_dict(config_data)


@dataclass
class Catalog(object):
    entries: dict[str, 'CatalogEntry']
    path: str = None

    def add_entry(self, name: str, path_file: str, path_thumbnail: str = None):
        # normalize file path key
        path_file = normalize_user_path(path_file)

        # re-use entry if it already exists
        is_new = True
        if path_file in self.entries:
            entry = self.entries[path_file]
            entry.name = name
            is_new = False
            path_dst = entry.path_thumbnail
        else:
            entry = CatalogEntry(name)
            path_dst = None

        # upload thumbnail
        if path_thumbnail and os.path.isfile(path_thumbnail):
            # this is a new thumbnail, create a unique name to save it
            if not path_dst:
                ext = os.path.splitext(path_thumbnail)[-1]
                name_unique = f'{uuid4().hex}{ext}'

                config = Config.load()
                path_dst = os.path.join(config.dir_root, config.dir_thumbnails)
                path_dst = os.path.expanduser(path_dst)
                os.makedirs(os.path.dirname(path_dst), exist_ok=True)
                path_dst = os.path.join(path_dst, name_unique)

            # upload thumbnail
            shutil.copy(path_thumbnail, os.path.expanduser(path_dst))
            entry.path_thumbnail = normalize_user_path(path_dst)
            log(f'Uploaded {name}\'s thumbnail to {entry.path_thumbnail}')

        # store entry data
        self.entries[path_file] = entry
        log(f'Added entry for {name}')

        return is_new

    @staticmethod
    def load(path: str = None):
        if not path:
            config = Config.load()
            path = os.path.join(config.dir_root, config.catalog_name)

        # try to read the catalog
        data = read_json(path, verbose=False)

        # return an empty catalog
        if not data:
            return Catalog.empty(path)

        # parse catalog
        entries = {}
        for path_file in data:
            entry_data = data[path_file]
            entry = CatalogEntry.from_dict(entry_data)
            if entry:
                entries[path_file] = entry

        log(f'Loaded catalog from {path}')
        return Catalog(entries, path)

    def save(self, path: str = None):
        if path:
            self.path = path

        # save to json file
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(os.path.expanduser(self.path), 'w') as file:
            json.dump(self.to_dict(), file, indent=2)

        log(f'Saved catalog to {self.path}')
        return True

    @staticmethod
    def empty(path: str) -> 'Catalog':
        return Catalog({}, path)

    def to_dict(self):
        return {
            path_asset:self.entries[path_asset].to_dict()
            for path_asset in self.entries
        }


@dataclass
class CatalogEntry(object):
    name: str
    path_thumbnail: str = None

    def __post_init__(self):
        if self.path_thumbnail:
            self.path_thumbnail = normalize_user_path(self.path_thumbnail)

    @staticmethod
    def from_dict(data: dict):
        try:
            item_name = data['name']
        except KeyError:
            log(f'Asset catalog entry is missing required data :: {item}', level=Level.ERROR)
            return None
        item_thumbnail = get_or_default(data, 'path_thumbnail', None)

        return CatalogEntry(item_name, item_thumbnail)

    def to_dict(self):
        return {
            'name': self.name,
            'path_thumbnail': self.path_thumbnail,
        }


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


def main():
    catalog = Catalog.load()
    catalog.add_entry('sgda', 'C:/Users/Nick/test.ma', r'C:\Users\Nick\Downloads\SGDA_Letters_SQ.png')
    catalog.save()
    print(catalog)


if __name__ == '__main__':
    main()
