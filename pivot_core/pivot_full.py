#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
from collections import OrderedDict
import requests
from copy import deepcopy
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Markdown, Javascript, FileLink, FileLinks, Image
import pandas as pd
from pivot_core._version import __desc__

# Widgets
from ipywidgets import GridspecLayout, widgets
import jupyter_integrations_utility as jiu
try:
    from pivottablejs import pivot_ui
except:
    print("Could not import pivottablejs")

from addon_core import Addon

@magics_class
class Pivot(Addon):
    # Static Variables

    magic_name = "pivot"
    name_str = "pivot"
    custom_evars = []

    myopts = {}


    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Pivot, self).__init__(shell, debug=debug)
        self.debug = debug

        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)

        runcode = "try:\n    from pivottablejs  import pivot_ui\nexcept:\n    pass\n"
        runres = shell.ex(runcode)

        try:
            a = type(pivot_ui)
        except:
            print("pivottablejs doesn't seem to be installed, you will need this")

# Display Help can be customized

    def customHelp(self, curout):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout
        out += table_header
        out += f"| {m} pivot_df | Run Pivot Table UI  on pivot_df |\n"
        out += "\n\n"
        out += "\n"
        return out

    def retCustomDesc(self):
        return __desc__


    # This is the magic name.
    @line_cell_magic
    def pivot(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations. 
                if line.lower().find("pivot") == 0:
                    newline = line.replace("pivot", "").strip()
                    pivot_ui(self.ipy.user_ns[newline])
                elif line.strip().split(" ")[0] in self.ipy.user_ns:
                    self.pivot("pivot " + line.strip())
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)
