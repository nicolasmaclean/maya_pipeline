#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Evaluate file paths using formulas from text files.
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
from enum import Enum
import json
import os

# Internal
# from haymaker.log import log, Level

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


_repo: 'FormulaRepo' = None
def eval_formula(formula_name: str, expand_user=True, **kwargs) -> str:
    # lazy load formula repo
    global _repo
    if not _repo:
        _repo = FormulaRepo.load()

    path = _repo.eval(formula_name, **kwargs)
    if expand_user:
        path = os.path.expanduser(path)
    return path


def _read_json(path: str, verbose: bool = True):
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


#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------- ENUMS --#


class ReservedVariable(Enum):
    @classmethod
    def get_default(cls):
        i = iter(cls)
        next(i)
        return next(i)

    @classmethod
    def try_to_resolve(cls, value, **kwargs):
        if cls.DEFAULT.value == value:
            # allow override from kwargs
            if cls.DEFAULT.value in kwargs:
                return kwargs[cls.DEFAULT.value].value
            return cls.get_default().value

        i = iter(cls)
        next(i)
        for e in i:
            if e.name.lower() == value:
                # allow override from kwargs
                if cls.DEFAULT.value in kwargs:
                    return kwargs[cls.DEFAULT.value].value
                return e.value

        return None


class Drive(ReservedVariable):
    DEFAULT = 'drive'
    BOX = '~/Box/Capstone_Uploads'


class Disk(ReservedVariable):
    DEFAULT = 'disk'
    CONFIG = '|drive|/13_Tech/config'
    CODE = '|drive|/13_Tech/haymaker'


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------- EXCEPTIONS --#


class FormulaException(Exception): pass
class FormulaNotFoundError(FormulaException): pass
class FormulaArgumentError(FormulaException): pass
class FormulaDuplicateError(FormulaException): pass
class FormulaEvaluationError(FormulaException): pass


#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#


class FormulaRepo(object):
    """
    Container for runtime generated and evaluated file path formulas. Formulas can build
    on each other, and ReservedVariables and kwargs can be used to manipulate the
    evaluation of formulas.
    """
    RESERVED_KEYWORDS = [
        Drive, Disk
    ]

    def __init__(self):
        self.formulas = {}
        self.formula_prefixes = []

    def eval(self, formula_name: str, **kwargs) -> str:
        """
        Finds the requested formula in this repo and returns a resolved value.

        Variables in a formula are resolved in this order: Reserved keywords (Drive and
        Disk), kwarg, formulas. A variable in the formula is wrapped with |. When reserved
        keywords are evaluated, kwargs can be used to override them.
            - "|box|test.txt" would have a single variable of the name box.
            - "|var|test.txt" would require a "var" kwarg to be evaluated because var is
               not reserved.

        :param formula_name: the name of the formula you would like to evaluate.
        :param kwargs: named variables that can be used during evaluation.

        :returns: a resolved formula based on the variables.
        """
        # get formula
        formula_name = self._remove_prefix(formula_name)
        try:
            formula = self.formulas[formula_name]
        except KeyError:
            raise FormulaNotFoundError(f'Could not find a formula for {formula_name}.')
        return self._eval(formula, **kwargs)

    @staticmethod
    def load(path: str = None):
        """
        Load a FormulaRepo from json. It will default to ./formulas.json.
        """
        # default to ./formulas.json
        if not path or not os.path.isfile(path):
            path = os.path.dirname(__file__)
            path = os.path.join(path, 'formulas.json')

        # read and file
        config_data = _read_json(path)
        if not config_data:
            raise RuntimeError('Unable to read a formulas.json.')

        # create an instance of the repo with this data
        repo = FormulaRepo()
        try:
            repo.formula_prefixes = config_data['formula_prefixes']
            for formula in config_data['formulas']:
                repo._add_formula(formula, config_data['formulas'][formula])
        except KeyError:
            # log(f'{path} seems to be missing formula data.', level=Level.WARN)
            return None

        # log(f'Read formulas from {path}')
        return repo

    def get_formula(self, formula_name: str):
        """
        Safely finds the formula with this key.
        """
        try:
            formula_name = self._remove_prefix(formula_name)
            return self.formulas[formula_name]
        except KeyError:
            return None

    def _eval(self, formula: str, **kwargs):
        # replace variables as necessary
        resolved = ""
        variable = None
        for c in formula:
            # start/stop variable evaluation
            if c == '|':
                # variable name is starting
                if variable is None:
                    variable = ""
                # variable name is done
                # evaluate the variable
                else:
                    resolved_variable = self._resolve_variable(variable, **kwargs)
                    resolved += self._eval(resolved_variable, **kwargs)
                    variable = None

                continue

            # collect variable name or non-variable characters
            if variable is None:
                resolved += c
            else:
                variable += c

        if variable is not None:
            raise FormulaEvaluationError(f"Missing closing '|' in {formula}")

        return resolved

    def _resolve_variable(self, variable, **kwargs):
        # check keywords
        for keyword in self.RESERVED_KEYWORDS:
            if value := keyword.try_to_resolve(variable, **kwargs):
                return value

        # check kwargs
        if variable in kwargs:
            return kwargs[variable]

        # check formulas
        if formula := self.get_formula(variable):
            return self._eval(formula, **kwargs)

        # unknown variable
        raise FormulaArgumentError(
            f'eval() is missing an argument for {variable}.'
        )

    def _remove_prefix(self, s):
        for prefix in self.formula_prefixes:
            if s.startswith(prefix):
                return s[len(prefix)+1:]
        return s

    def _add_formula(self, key: str, formula: str):
        key = self._remove_prefix(key)
        if key in self.formulas:
            raise FormulaDuplicateError(f'The {key} formula already exists.')
        self.formulas[key] = formula

    def __str__(self):
        return f'<FormulaRepo {self.__dict__}>'


#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#

def main():
    repo = FormulaRepo.load()
    print(repo.eval('asset_library'))
    print(repo.eval('asset_catalog'))
    print(repo.eval('asset_catalog', drive=Drive.LOCAL, disk=Disk.STORE))
    print(repo.eval('asset_library', drive=Drive.LOCAL))




if __name__ == '__main__':
    main()
