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
from profile._version import __desc__

# Widgets
from ipywidgets import GridspecLayout, widgets
import jupyter_integrations_utility as jiu
try:
    from pandas_profiling import ProfileReport
except:
    print("Could not import pandas_profiling")

from addon_core import Addon

@magics_class
class Profile(Addon):
    # Static Variables

    magic_name = "profile"
    name_str = "profile"
    custom_evars = []

    custom_allowed_set_opts = ['profile_max_rows_full']


    myopts = {}
    myopts['profile_max_rows_full'] = [10000, "Row threshold for doing full analysis. Over there and we default to minimal analysis with a warning"]


    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Profile, self).__init__(shell, debug=debug)
        self.debug = debug

        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)
#        shell.user_ns['profile_var'] = self.creation_name

        runcode = "try:\n    from pandas_profiling import ProfileReport\nexcept:\n    pass\n"
        runres = shell.ex(runcode)

        try:
            a = type(ProfileReport)
        except:
            print("pandas_profiling doesn't seem to be installed, you will need this")

# Display Help can be customized

    def customHelp(self, curout):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout
        out += table_header
        out += "| %s | Run Pandas Profiler on profiledf |\n" % (m + " $profiledf")
        out += "| %s | Run Pandas Profile on profiledf with a title of 'Your Title' |\n" % (m + " %profiledf Your Title")
        out += "\n\n"
        out += "**The last report run is stored in a pandas profile variable named prev_profile**\n"
        out += "\n"
        return out

    def retCustomDesc(self):
        return __desc__




    def runProfile(self, line):
        line = line.replace("\r", "")
        tar =line.split(" ")
        if len(tar) == 1:
            mydfname = tar[0]
            mytitle = "Adhoc profile report for %s" % mydfname
        elif len(tar) > 1:
            mydfname = tar[0]
            mytitle = " ".join(tar[1:])
        else:
            mydfname = 'error'
            mytitle = 'title error'

        pd.set_option("mode.chained_assignment", None)
        if self.debug:
            print("mydfname: %s" % mydfname)
            print("mytitle: %s" % mytitle)

        try:
            mydf = self.ipy.user_ns[mydfname]
        except:
            mydf = None
        if isinstance(mydf, pd.DataFrame):
            if len(mydf) <= self.opts['profile_max_rows_full'][0]:
                tprofile = ProfileReport(mydf, title=mytitle, explorative=True)
            else:
                print("Dataframe %s has more rows (%s) than the profile_max_rows_full (%s) Variable - Performing Minimal Analysis" % (mydfname, len(mydf), self.opts['profile_max_rows_full'][0]))
                tprofile = ProfileReport(mydf, title=mytitle, minimal=True)
            self.ipy.user_ns['prev_profile'] = tprofile
            display(tprofile)
        else:
            print("Variable %s does not appear to be a valid Pandas Dataframe in current kernel" % mydfname)
        pd.set_option("mode.chained_assignment", "warn")


    # This is the magic name.
    @line_cell_magic
    def profile(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations. 
                if line.lower().find("profile") == 0:
                    newline = line.replace("profile", "").strip()
                    self.runProfile(newline)
                elif line.strip().split(" ")[0] in self.ipy.user_ns:
                    self.profile("profile " + line.strip())
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)
