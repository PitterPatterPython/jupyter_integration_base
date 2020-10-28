#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
import pandas as pd
from copy import deepcopy


# Plotly
try:
    from pandas_profiling import ProfileReport
except:
    print("Could not import pandas_profiling")

from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Javascript, FileLink, FileLinks, Image

# Widgets
from ipywidgets import GridspecLayout, widgets


@magics_class
class Profile(Magics):
    # Static Variables
    ipy = None              # IPython variable for updating and interacting with the User's notebook
    debug = False           # Enable debug mode
    base_allowed_set_opts = ['max_rows_full']
    # Variables Dictionary
    opts = {}
    opts['max_rows_full'] = [10000, "Row threshold for doing full analysis. Over there and we default to minimal analysis with a warning"]

    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first. 
    # This is because they are designed to be self documenting. 
    # Each option item is actually a list of two length. 
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description. 


    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables. 
    def __init__(self, shell, debug=False, *args, **kwargs):
        self.debug = debug
        super(Profile, self).__init__(shell)
        self.ipy = get_ipython()
        try:
            a = type(ProfileReport)
        except:
            print("pandas_profiling doesn't seem to be installed, you will need this")
 # This is the magic name.
    @line_cell_magic
    def profile(self, line, cell=None):

        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)

        if cell is None:
            line = line.replace("\r", "")
            tar =line.split(" ")
            if len(tar) == 1:
                dfname = tar[0]
                mytitle = "Adhoc profile report for %s" % dfname
            elif len(tar) > 1:
                dfname = tar[0]
                mytitle = " ".join(tar[1:])
            else:
                dfname = 'error'
                mytitle = 'title error'

            if dfname == "help" or dfname == "":
                self.printHelp()
            elif dfname == "set":
                self.setvar(line)
            elif dfname == "debug":
                self.debug = not self.debug
            else:
                pd.set_option("mode.chained_assignment", None)
                try:
                    if self.debug:
                        print("dfname: %s" % dfname)
                        print("mytitle: %s" % mytitle)
                    curdf = self.ipy.user_ns[dfname]
                except:
                    curdf = None
                if self.debug:
                    print(type(curdf))
                if isinstance(curdf, pd.DataFrame):
                    if len(curdf) <= self.opts['max_rows_full'][0]:
                        tprofile = ProfileReport(curdf, title=mytitle, explorative=True)
                    else:
                        print("Dataframe %s has more rows (%s) than the max_rows_full (%s) - Performing Minimal Analysis" % (dfname, len(curdf), self.opts['max_rows_full'][0]))
                        tprofile = ProfileReport(curdf, title=mytitle, minimal=True)
                    self.ipy.user_ns['prev_profile'] = tprofile
                    display(tprofile)
                else:
                    print("Variable %s does not appear to be a valid Pandas Dataframe in current kernel" % dfname)
                pd.set_option("mode.chained_assignment", "warn")


        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("Cell magics for %profile not used at this time")


    def printHelp(self):
        print("Profiling with pandas-profiling")
        print("--------------------------------")
        print("")
        print("Current max_rows_full: %s" % self.opts['max_rows_full'][0])
        print("")
        print("If your dataframe is less than 'max_rows_full' we will run a full analysis. If it's more, we run the minimal analysis")
        print("If you want to change this type:")
        print("%profile set max_rows_full YOUR_NEW_NUMBER")
        print("")
        print("%profile debug             - Toggles Debug mode")
        print("")
        print("%profile yourdf            - Run the profile on dataframe named yourdf with a default title")
        print("%profile yourdf Your Title - Run the profile on dataframe named yourdf with 'Your Title' as the tile")
        print("")
        print("The last run profile is also available in a variable called prev_profile.  It is independent of integration, it's just the last run profile")
        print("")
        
##### setvar should only exist in the base_integration
    def setvar(self, line):

        allowed_opts = self.base_allowed_set_opts

        tline = line.replace('set ', '')
        tkey = tline.split(' ')[0] # Keys can't have spaces, values can
        tval = tline.replace(tkey + " ", "")
        if tval == "False":
            tval = False
        if tval == "True":
            tval = True
        try:
            nval = int(tval)
            tval = nval
        except:
            pass
        if tkey in allowed_opts:
            self.opts[tkey][0] = tval
        else:
            print("You tried to set variable: %s - Not in Allowed options!" % tkey)
