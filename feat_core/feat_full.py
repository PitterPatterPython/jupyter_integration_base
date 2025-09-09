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
from feat_core._version import __desc__

# Widgets
from ipywidgets import GridspecLayout, widgets
import jupyter_integrations_utility as jiu
import jupyter_integrations_utility.funcdoc
from jupyter_integrations_utility.feat_calc import *
from addon_core import Addon

@magics_class
class Feat(Addon):
    # Static Variables

    magic_name = "feat"
    name_str = "feat"
    custom_evars = []

    custom_allowed_set_opts = ['feat_desc']


    myopts = {}
    myopts['feat_desc'] = ["I describe", "A statement of description"]


    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Feat, self).__init__(shell, debug=debug)
        self.debug = debug

        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)
        this_file_fx = feat_file_fx

        self.ipy.ex("from jupyter_integrations_utility.feat_calc import *\n")

        #self.feature_calc_help("basic")

#        shell.user_ns['profile_var'] = self.creation_name

        #runcode = "try:\n    from pandas_profiling import ProfileReport\nexcept:\n    pass\n"
        #runres = shell.ex(runcode)

# Display Help can be customized

    def customHelp(self, curout):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout
        out += table_header
        out += f"| {m + ' functions'} |  List all functions|\n"
        out += f"| {m + ' functions output_features'} |  List docs for output_features function|\n"
        out += "\n\n"
        return out

    def retCustomDesc(self):
        return __desc__



    def feature_calc_help(self, func_name=None, debug=False):

   # Variables
        title = "Feature Description, Application, Calculation, and Display Functions"     # The title of this shared function file. (Good to group them, queries, features, enrichment, utility etc)
        help_func = "feature_calc_help"          # The name of the help function (i.e. this function i.e shared_function_help)
        exp_func = "reapply_all"                     # An example function you can use to demostrate how to get help on a function (It should exist below)
        functions_name = "feature_calc" # The name of this file you can use in other files to check if this one is loaded (if there are dependent functions



    #
    # Function Dictionary
    #
    # This is the list of functions you are sharing.
    # Each dictionary key is a group title, and then the value is list of the function names.
    # This has to be changed if you want to add a function into the listed functions in the help file
    #

   # Custom code for current include

        doc_functions = {
        "Helper Functions": [
            "reapply_all",
            "ret_var_name",
            "increase_date_window"
        ],
        "General Feature Functions": [
            "feature_compare",
            "apply_features",
            "apply_custom_clauses",
            "parse_custom_clause",
            "ret_custom_clause_group",
            "ret_custom_clause_desc",
            "calculate_features",
            "output_features"
        ]
        }


# Do not change the rest of this function
        if debug:
            print("Running with debug")

        jupyter_integrations_utility.funcdoc.main_help(title, help_func, doc_functions, globals(), exp_func=exp_func, func_name=func_name, magic_src=self.magic_name, debug=debug)
#    if functions_name not in loaded_helpers:
#        loaded_helpers.append(functions_name)




    # This is the magic name.
    @line_cell_magic
    def feat(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations. 
                if line.lower().find("functions") == 0:
                    newline = line.replace("functions", "").strip()
                    if newline == "":
                        self.feature_calc_help(None)
                    else:
                        self.feature_calc_help(newline)
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)
