#!/usr/bin/env python
# SETMODE 777

# ----------------------------------------------------------------------------------------#
# ------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    GUI for accessing and managing a maya_asset_library.

:applications:
    Maya
"""


# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------- IMPORTS --#

# Built-In
import os

# Third Party

# Internal
from haymaker.asset_library.utils import Catalog, CatalogEntry
from haymaker.log import log
from haymaker.formula_manager import eval_formula
from haymaker import widgets


# ----------------------------------------------------------------------------------------#
# --------------------------------------------------------------------------- FUNCTIONS --#

# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------- CLASSES --#


class AssetThumbnail(widgets.Label):
    def __init__(self, entry):
        self.path_thumbnail = os.path.expanduser(entry.path_thumbnail)
        super().__init__(self.path_thumbnail, is_path=True, width=150)
        self.setFixedSize(150, 150)

    def mousePressEvent(self, event):
        print('hi')
        super().mousePressEvent(event)


class AssetLibrary(widgets.Dialog):
    default_title = 'Asset Library'
    default_size = (540, 750)
    size_is_fixed = True

    def __init__(self):
        self.lbl_selected = None
        super().__init__()

    def init(self, **kwargs):
        vb_main = widgets.VLayout(self)

        # grid of assets in library
        from PySide2 import QtWidgets
        from PySide2.QtCore import Qt

        scroll = QtWidgets.QScrollArea()
        vb_main.addWidget(scroll)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        wrapper_grid = widgets.Widget()
        grid = widgets.GridLayout(wrapper_grid)
        scroll.setWidget(wrapper_grid)
        entry = CatalogEntry(
            'temp',
            r'C:\Users\Nick\Box\Capstone_Uploads\13_Tech\haymaker\resources\full/'
            'file_not_found.png'
        )

        for r in range(5):
            for c in range(3):
                lbl = AssetThumbnail(entry)
                grid.addWidget(lbl, r, c)

        # button to reference asset
        hb_buttons = widgets.HLayout(vb_main)
        self.lbl_selected = widgets.Label('', hb_buttons)
        hb_buttons.addStretch()
        widgets.Button('Reference Asset(s)', self.reference_selected, hb_buttons)

        super().init()

    def reference_selected(self):
        print('clicked')


# ----------------------------------------------------------------------------------------#
# -------------------------------------------------------------------------------- MAIN --#


def main():
    app = widgets.get_app()
    gui = AssetLibrary()
    widgets.run_app(app)


if __name__ == '__main__':
    main()
