#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
import pandas as pd

from collections import OrderedDict

from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML

from IPython.display import display_html, display, Javascript, FileLink, FileLinks, Image
import ipywidgets as widgets

try:
    import qgrid
except:
    pass    


#@magics_class
class Integration(Magics):
    # Static Variables
    ipy = None              # IPython variable for updating things
    session = None          # Session if ingeration uses it
    connected = False       # Is the integration connected
    name_str = ""
    connect_pass = ""       # Connection password is special as we don't want it displayed, so it's a core component
    proxy_pass = ""         # If a proxy is required, we need a place for a password. It can't be in the opts cause it would be displayed. 
    debug = False           # Enable debug mode
    env_pre = "JUPYTER_"    #  Probably should allow this to be set by the user at some point

    base_allowed_set_opts = ['pd_display.max_columns', 'pd_display.max_rows', 'pd_max_colwidth', 'pd_display_grid', 'pd_display_idx']
    pd_set_vars = ['pd_display.max_columns', 'pd_display.max_rows', 'pd_max_colwidth', 'pd_display_grid']
    # Variables Dictionary
    opts = {}
    global_evars = ['proxy_host', 'proxy_user']

    # Option Format: [ Value, Description]

    # Pandas Variables
    opts['pd_display_idx'] = [False, "Display the Pandas Index with output"]
    opts['pd_replace_crlf'] = [True, "Replace extra crlfs in outputs with String representations of CRs and LFs"]
    opts['pd_max_colwidth'] = [50, 'Max column width to display']
    opts['pd_display.max_rows'] = [1000, 'Number of Max Rows']
    opts['pd_display.max_columns'] = [None, 'Max Columns']
    opts['pd_display_grid'] = ["html", 'How pandas DF should be displayed']
    opts['pd_beaker_bool_workaround'] = [True, 'Look for Dataframes with bool columns, and make it object for display in BeakerX']

    pd.set_option('display.max_columns', opts['pd_display.max_columns'][0])
    pd.set_option('display.max_rows', opts['pd_display.max_rows'][0])
    pd.set_option('max_colwidth', opts['pd_max_colwidth'][0])

            

    # Class Init function - Obtain a reference to the get_ipython()
    def __init__(self, shell, *args, **kwargs):
        super(Integration, self).__init__(shell)
        self.ipy = get_ipython()
        self.session = None
        self.load_env(self.global_evars)


#### This won't be overridden

    def load_env(self, evars):
        for v in evars:
            try:
                tvar = os.environ[self.env_pre + v.upper()]
            except:
                tvar = ""
            self.opts[v] = tvar
            tvar = ""

##### connect should be overwriittn by custom integrarion
    def connect(self, prompt=False):
        pass

##### auth should be overwriittn by custom integrarion
    def auth(self):
        self.session = None
        result = 0
        return result

##### validateQuery should be overwriittn by custom integrarion - without customer validateQuery, all queries are valid
    def validateQuery(self, query):
        bRun = True
        bReRun = False
        return bRun

##### customQuery should be overwriittn by custom integrarion
    def customQuery(self, query):
        return None, 0, "Failure - Not written"
    
##### Override this in an actual integration
    def customHelp(self):
        print("This would be custom help for the integration")


################################################################


##### This is the base integration for line magic (single %), it handles the common items, and if the magic isn't common, it sends back to the custom integration to handle
    def handleLine(self, line):
        bMischiefManaged = False
        # Handle all common line items or return back to the custom integration
        if line == "":
            self.displayHelp()
            bMischiefManaged = True
        elif line.lower() == "status":
            self.retStatus()
            bMischiefManaged = True
        elif line.lower() == "debug":
            print("Toggling Debug from %s to %s" % (self.debug, not self.debug))
            self.debug = not self.debug
            bMischiefManaged = True
        elif line.lower() == "disconnect":
            bMischiefManaged = True
            self.disconnect()
        elif line.lower() == "connect alt":
            self.connect(True)
            bMischiefManaged = True
        elif line.lower() == "connect":
            self.connect(False)
            bMischiefManaged = True
        elif line.lower().find('set ') == 0:
            self.setvar(line)
            bMischiefManaged = True
        else:
            pass
        return bMischiefManaged 

##### handleCell should NOT need to be overwritten, however, I guess it could be
    def handleCell(self, cell):
        if self.connected == True:
            result_df, qtime, status = self.runQuery(cell)
            if status.find("Failure") == 0:
                print("Error: %s" % status)
            elif status.find("Success - No Results") == 0:
                print("No Results returned in %s seconds" % qtime)
            elif status.find("ValidationError") == 0:
                print("Validation Error")
            else:
                self.ipy.user_ns['prev_' + self.name_str] = result_df
                if result_df is not None:
                    mycnt = len(result_df)
                else:
                    mycnt = 0
                print("%s Records in Approx %s seconds" % (mycnt,qtime))
                print("")
                if mycnt <= int(self.opts['pd_display.max_rows'][0]):
                    if self.debug:
                        print("Testing max_colwidth: %s" %  pd.get_option('max_colwidth'))
                    if self.opts['pd_display_grid'][0] == "qgrid":
                        display(qgrid.show_grid(result_df))
                    else:
                        display(HTML(result_df.to_html(index=self.opts['pd_display_idx'][0])))
                else:
                    print("Number of results (%s) greater than pd_display.max_rows(%s)" % (mycnt, self.opts['pd_display.max_rows'][0]))
        else:
            print(self.name_str.capitalize() + " is not connected: Please see help at %" + self.name_str)

        
        
##### Leave runQuery in the base integration - it handles query timing, instead customize customerQuery in actual integration
    def runQuery(self, query):

        mydf = None
        status = "-"
        starttime = int(time.time())
        run_query = self.validateQuery(query)

        if run_query:
            if self.connected == True:
                mydf, status = self.customQuery(query)
            else:
                mydf = None
                status = "%d Not Connected" % self.name_str.capitalize()
                myjson = None
        else:
            status = "ValidationError"
            mydf = None
            myjson = None
        endtime = int(time.time())
        query_time = endtime - starttime

        return mydf, query_time, status
##### displayHelp should only be in base. It allows a global level of customization, and then calls the custom help in each integration that's unique
    def displayHelp(self):
        print("***** Jupyter Integtations Help System")
        print("")
        self.customHelp()




#### retStatus should not be altered this should only exist in the base integration
    def retStatus(self):

        print("Current State of %s Interface:" % self.name_str.capitalize())
        print("")
        print("{: <30} {: <50}".format(*["Connected:", str(self.connected)]))
        print("{: <30} {: <50}".format(*["Debug Mode:", str(self.debug)]))

        print("")

        print("Display Properties:")
        print("-----------------------------------")
        for k, v in self.opts.items():
            if k.find("pd_") == 0:
                try:
                    t = int(v[1])
                except:
                    t = v[1]
                if v[0] is None:
                    o = "None"
                else:
                    o = v[0]
                myrow = [k, o, t]
                print("{: <30} {: <50} {: <20}".format(*myrow))
                myrow = []


        print("")
        print("%s Properties:" %  self.name_str.capitalize())
        print("-----------------------------------")
        for k, v in self.opts.items():
            if k.find(self.name_str + "_") == 0:
                if v[0] is None:
                    o = "None"
                else:
                    o = str(v[0])
                myrow = [k, o, v[1]]
                print("{: <30} {: <50} {: <20}".format(*myrow))
                myrow = []

##### setvar should only exist in the base_integration
    def setvar(self, line):

        allowed_opts = self.base_allowed_set_opts + self.custom_allowed_set_opts

        tline = line.replace('set ', '')
        tkey = tline.split(' ')[0]
        tval = tline.split(' ')[1]
        if tval == "False":
            tval = False
        if tval == "True":
            tval = True
        if tkey in allowed_opts:
            self.opts[tkey][0] = tval
            if tkey in self.pd_set_vars:
                try:
                    t = int(tval)
                except:
                    t = tval
                pd.set_option(tkey.replace('pd_', ''), t)
        else:
            print("You tried to set variable: %s - Not in Allowed options!" % tkey)

