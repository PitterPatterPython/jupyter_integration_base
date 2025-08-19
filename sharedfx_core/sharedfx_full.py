#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import textwrap
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
# Widgets
from ipywidgets import GridspecLayout, widgets
import jupyter_integrations_utility as jiu
import importlib
from sharedfx_core._version import __desc__

from addon_core import Addon

@magics_class
class SharedFX(Addon):
    # Static Variables
    magic_name = "sharedfx"
    name_str = "sharedfx"
    mods = {}

    custom_evars = []

    custom_allowed_set_opts = []

    myopts = {}
#    myopts['sharedfx_max_full_results'] = [1, "When searching, if your results are above this number it only returns the function name and keywords, otherwise it returns full description"]
#    myopts['sharedfx_ver_check_delta'] = [86400, "Number of seconds between version checks - 86400 is one day."]
#    myopts['sharedfx_addon_dir'] = ['~/.ipython/integrations/' + name_str, "Directory for sharedmod caching/configs"]
#    myopts['sharedfx_cache_filename'] = ["modver.cache", "Filename for sharedmod caching"]
#    evars = []


    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(SharedFX, self).__init__(shell, debug=debug)
        self.debug = debug

        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]

#        self.addon_evars += ["_url_"]

        self.load_env(self.custom_evars) # Called in addon core - Should make it so mods are generic. 


    def handleSearch(self, l, c):
        if self.debug:
            print("Line: %s" % l)
            print("Cell: %s" % c)
        myScore = self.searchFuncs(c, l)
        if self.debug:
            print("Raw myScore: %s" % myScore)
        sortedScore = dict(sorted(myScore.items(), key=lambda item: item[1][1], reverse=True))
        out = ""
        out += "## Function Search Results\n"
        out += "------------\n"
        out += "### Search Term: %s\n" % c.strip()
        out += "----------------\n"
        for x in sortedScore.keys():
            out += "<details>\n<summary>%s - Score: %s</summary>\n\n" % (x, sortedScore[x][1]) 
            out += self.retSingleFunc(x)
            out += "</details>\n\n"

        out += "\n\n"
        return out




    def customHelp(self, curout):
        n = self.magic_name
        m = "%" + n
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout

        out += "## %s usage\n" % n
        out += "---------------\n"
        out += "\n"
        out += "### %s line magic\n" % (m)
        out += "---------------\n"
        out += "Interacting with specfics parts of the shared function system\n\n"
        out += table_header
        out += "| %{m} mods | List the requested modules, and their relavent information including import status |\n"
        out += "| %{m} imports | Show the actual import lines (in the next cell) for the successfully imported modules |\n"
        out += "| %{m} list | Show all documented functions handled by shared funcs |\n"
        out += "| %{m} list modname | Show all documented functions in the 'modname' module |\n"
        out += "| %{m} list `fxname` | Show the documentation for the 'fxname' function as formatted in list |\n"
        out += "\n\n"
       # out += "### %s cell magic\n" % (mq)
       # out += "-------------------\n"
       # out += "Running searches and obtaining results back from the shared function system\n\n"
       # out += table_header
       # out += "| %s | 'scope' is the search scope (name, kw, desc, author) (can provide multiple, leave blank for all) and the 'query' are the keywords searched |\n" % (mq + " scope<br>query")
       # out += "| %s | Search for any functions related to geoip |\n" % (mq + "<br>geoip")
       # out += "| %s | Search for any function where the description has  active directory |\n" % (mq + " desc<br>active directory")
       # out += "\n"

        return out

    def retCustomDesc(self):
        return __desc__

    # This is the magic name.
    @line_cell_magic
    def sharedfx(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations.
                if line.find("display") == 0:
                    jiu.displayMD(self.displayFuncs(line.replace("display", "").strip()))
                else:
                    print("Unknown line magic for funcs")
        else: # This is a cell (or a cell + line) call
            jiu.displayMD(self.handleSearch(line, cell))


