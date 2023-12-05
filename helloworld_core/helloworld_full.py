#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
import textwrap
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

from helloworld_core._version import __desc__
from addon_core import Addon

@magics_class
class Helloworld(Addon):
    # Static Variables

    magic_name = "helloworld"
    name_str = "helloworld"
    custom_evars = []

    # Addons required to be loaded
    req_addons = ['helloworld', 'display', 'persist', 'profile', 'sharedfunc', 'vis', 'namedpw', 'feat', 'pyvis', 'pivot']
    req_full_addons = ['display', 'namedpw']
    custom_allowed_set_opts = []


    myopts = {}
#    myopts['profile_max_rows_full'] = [10000, "Row threshold for doing full analysis. Over there and we default to minimal analysis with a warning"]


    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Helloworld, self).__init__(shell, debug=debug)
        self.debug = debug

        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)
        if 'jupyter_loaded_addons' not in self.ipy.user_ns:
            self.ipy.user_ns['jupyter_loaded_addons'] = {}
        self.ipy.user_ns['jupyter_loaded_addons']['helloworld'] = 'helloworld_full'
        self.check_req_addons()
        # Loading doc_and_batch
#        self.ipy.ex("from helloworld_core.doc_and_batch import *\n")
#        self.ipy.ex("from jupyter_integrations_utility.doc_and_batch import *\n")
        self.ipy.ex("from jupyter_integrations_utility.funcdoc import *\n")
        self.ipy.ex("from jupyter_integrations_utility.batchquery import *\n")

        try:
            env_dir = os.environ['VIRTUAL_ENV']
        except:
            print("No VIRTUAL_ENV directory found - Config not loaded")
            env_dir = None

        if 'integrations_cfg' not in self.ipy.user_ns and env_dir is not None:
            self.ipy.user_ns['integrations_cfg'] = jiu.load_json_config(file_loc=f"{env_dir}\\integrations_cfg.py")
        else:
            self.ipy.user_ns['integrations_cfg'] = None


#        shell.user_ns['helloworld_var'] = self.creation_name

    # We will maybe have to load helloworld  first
    def check_req_addons(self):
        for addon in self.req_addons:
            chk = addon
            if 'jupyter_loaded_addons' not in self.ipy.user_ns:
                self.ipy.user_ns['jupyter_loaded_addons'] = {}
            if chk not in self.ipy.user_ns['jupyter_loaded_addons'].keys():
                if self.debug:
                    print("%s not found in user_ns - Running" % chk)
                objname = addon.capitalize()
                corename = addon + "_core"
                if addon in self.req_full_addons:
                    varobjname = addon + "_full"
                else:
                    varobjname = addon + "_base"

                runcode = f"from {corename}.{varobjname} import {objname}\n{varobjname} = {objname}(ipy, debug={str(self.debug)})\nipy.register_magics({varobjname})\n"

                if self.debug:
                    print(runcode)
                res = self.ipy.ex(runcode)
                self.ipy.user_ns['jupyter_loaded_addons'][chk] = varobjname
            else:
                if self.debug:
                    print("%s found in user_ns - Not loading" % chk)






    def listIntsAdsMD(self):
        myout = ""
        myout += "\n"
        myout += "Additional help for each integration and addon can be found by running the magic string for each integration or addon\n"
        myout += "\n"
        myout += "### Installed Integrations and Addons\n"
        myout += "---------------\n"
        myout += "| Integration | Desc |   | Addon | Desc |\n"
        myout += "| ------ | ------ | --- | ----- | ---------|\n"

        myints = list(self.ipy.user_ns['jupyter_loaded_integrations'].keys())
        myadds = list(self.ipy.user_ns['jupyter_loaded_addons'].keys())
        for i in range(max(len(myints), len(myadds))):
            try:
                cn = self.ipy.user_ns['jupyter_loaded_integrations'][myints[i]]
                mn = self.ipy.user_ns[cn].magic_name
                myintdesc = self.ipy.user_ns[cn].retCustomDesc()
                myintdesc = "<br>".join(textwrap.wrap(myintdesc, 40))

                myint = "%" + mn
                myintstatus = str(True)
            except:
                myint = " "
                myintstatus = " "
                myintdesc = " "

            try:
                cn = self.ipy.user_ns['jupyter_loaded_addons'][myadds[i]]
                mn = self.ipy.user_ns[cn].magic_name
                myadddesc = self.ipy.user_ns[cn].retCustomDesc()
                myadddesc = "<br>".join(textwrap.wrap(myadddesc, 40))
                myadd = "%" + mn
                myaddstatus = str(True)
            except:
                myadd = " "
                myaddstatus = " "
                myadddesc = " "
            myout += "| %s | %s |   | %s | %s|\n" % (myint, myintdesc, myadd, myadddesc)
        myout += "\n"
        return myout

    def customHelp(self, curout):
        n = self.magic_name
        m = "%" + n
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout

        out += "\n"
        out += f"### {m} line magics\n"
        out += "---------------\n"
        out += table_header
        out += f"| {m + ' batch'} | Print the batch_query_help() (Same as typing batch_query_help() )  |\n"
        out += f"| {m + ' func'} | Print the function_doc_help() (Same as typing function_doc_help() )  |\n"
        out += f"| {m + ' go'} | Put the helloworld go (defined in the variable hello_go) into the next cell. You can specify this in an py file in the .ipython profile_default startup folder |\n"
        out += "\n\n"
        out += "\n"
        out += self.listIntsAdsMD()

        return out

    def retCustomDesc(self):
        return __desc__


    def fillGo(self, varname):

        fullvar = f"hello_{varname}"

        if fullvar in self.ipy.user_ns:
            self.ipy.set_next_input(self.ipy.user_ns[fullvar])
        elif fullvar == "hello_go":
            print(f"{fullvar} variable is not set - nothing to do")
        else:
            print("We shouldn't get here")



    # This is the magic name.
    @line_cell_magic
    def helloworld(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations.
                if line.lower().strip() == "go":
                    self.fillGo("go")
                elif line.lower().strip() == "batch":
                    self.ipy.ex("batch_query_help()")
                elif line.lower().strip() == "func":
                    self.ipy.ex("function_doc_help()")
                elif f"hello_{line.lower().strip()}" in self.ipy.user_ns:
                    self.fillGo(line.lower().strip())
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)



