#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Wrappers and utils for common PyQt classes/functions.
"""


# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------- IMPORTS --#

# Built-In

# Third Party

# Internal
from dorya.widgets import Dialog, get_resource_path, VLayout, Movie
from dorya.enums import WindowMode

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#


class BlaiseSurprise(Dialog):
    default_title = "TOP SECRET"
    # window_mode = WindowMode.Show

    default_size = (150, 170)
    default_position = (15, 625)

    def init(self, **kwargs):
        vb_main = VLayout(self)
        path_surprise = get_resource_path("TOPSECRET.gif", "full")
        Movie(path_surprise, parent=vb_main)

        super().init()

