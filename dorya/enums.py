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

# ONLY BUILT-IN IMPORTS ARE ALLOWED
# Built-In
from enum import Enum

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------- ENUMS --#


class _DisciplineName(object):
    def __init__(self, name_short, name_long=None):
        self.name_short = name_short
        self.name_long = name_long if name_long else name_short


class Discipline(Enum):
    MODEL = _DisciplineName('Model')
    SURFACE = _DisciplineName('Surface')
    RIG = _DisciplineName('Rig')
    LAY = _DisciplineName('Lay', 'Layout')
    ANI = _DisciplineName('Ani', 'Animation')
    LIT = _DisciplineName('Lit', 'Lighting')


class ResultType(Enum):
    SUCCESS = 'Success'
    WARNING = 'Warning'
    FAILURE = 'Failure'


class WindowMode(Enum):
    Show = 'Show'
    Modal = 'Modal'
    Exec = 'Exec'
