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
    ipy = None              # IPython variable for updating and interacting with the User's notebook
    session = None          # Session if ingeration uses it. Most data sets have a concept of a session object. An API might use a requests session, a mysql might use a mysql object. Just put it here. If it's not used, no big deal.  This could also be a cursor
    connection = None       # This is a connection object. Separate from a cursor or session it only handles connecting, then the session/cursor stuff is in session. 
    connected = False       # Is the integration connected? This is a simple True/False 
    name_str = ""           # This is the name of the integraton, and will be prepended with % for the magic, used in variables, uppered() for ENV variables etc. 
    connect_pass = ""       # Connection password is special as we don't want it displayed, so it's a core component
    proxy_pass = ""         # If a proxy is required, we need a place for a password. It can't be in the opts cause it would be displayed. 
    debug = False           # Enable debug mode
    env_pre = "JUPYTER_"    #  Probably should allow this to be set by the user at some point. If sending in data through a ENV variable this is the prefix

    base_allowed_set_opts = ['pd_display.max_columns', 'pd_display.max_rows', 'pd_max_colwidth', 'pd_display_grid', 'pd_display_idx', 'q_replace_a0_20', 'q_remove_cr', 'qg_defaultColumnWidth'] # These are the variables we allow users to set no matter the inegration (we should allow this to be a customization)

    pd_set_vars = ['pd_display.max_columns', 'pd_display.max_rows', 'pd_max_colwidth', 'pd_display_grid'] # These are a list of the custom pandas items that update a pandas object


    # Variables Dictionary
    opts = {}
    global_evars = ['proxy_host', 'proxy_user'] # These are the ENV variables we check with. We upper() these and then prepend env_pre. so proxy_user would check the ENV variable JUPYTER_PROXY_HOST and let set that in opts['proxy_host']


    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first. 
    # This is because they are designed to be self documenting. 
    # Each option item is actually a list of two length. 
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description. 

    # Pandas Variables
    opts['pd_display_idx'] = [False, "Display the Pandas Index with output"]
    opts['pd_replace_crlf'] = [True, "Replace extra crlfs in outputs with String representations of CRs and LFs"]
    opts['pd_max_colwidth'] = [50, 'Max column width to display when using pandas html output']
    opts['pd_display.max_rows'] = [1000, 'Number of Max Rows']
    opts['pd_display.max_columns'] = [None, 'Max Columns']
    opts['pd_display_grid'] = ["html", 'How pandas DF should be displayed']
    opts['qg_defaultColumnWidth'] = [200, 'The default column width when using qgrid']
    opts['q_replace_a0_20'] = [False, 'If this is set, we will run a replace for hex a0 replace with space (hex 20) on queries - This happens on lines and cells']
    opts['q_replace_crlf_lf'] = [True, 'If this is set, we replace crlf with lf (convert windows to unix line endings) on queries - This only happens on cells not lines']

    pd.set_option('display.max_columns', opts['pd_display.max_columns'][0])
    pd.set_option('display.max_rows', opts['pd_display.max_rows'][0])
    pd.set_option('max_colwidth', opts['pd_max_colwidth'][0])

            

    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables. 
    def __init__(self, shell, debug=False, pd_display_grid="html", *args, **kwargs):
        self.debug = debug
        super(Integration, self).__init__(shell)
        self.ipy = get_ipython()
        self.session = None
        self.load_env(self.global_evars)



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
        if self.opts['q_replace_a0_20'][0] == True:
            line = line.replace("\xa0", " ")

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
        if self.opts['q_replace_crlf_lf'][0] == True:
            cell = cell.replace("\r\n", "\n")
        if self.opts['q_replace_a0_20'][0] == True:
            cell = cell.replace("\xa0", " ")

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
                        if self.opts['pd_display_idx'][0] == True:
                            display(qgrid.show_grid(result_df, grid_options={'forceFitColumns': False, 'defaultColumnWidth': int(self.opts['qg_defaultColumnWidth'][0])}))
                        else:
                            # Hack to hide the index field
                            display(qgrid.show_grid(result_df, grid_options={'forceFitColumns': False, 'defaultColumnWidth': int(self.opts['qg_defaultColumnWidth'][0])}, column_definitions={ 'index': { 'maxWidth': 0, 'minWidth': 0, 'width': 0  } }))

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
            if k.find("pd_") == 0 or k.find("qg_") == 0 or k.find("q_") == 0:
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
        tkey = tline.split(' ')[0] # Keys can't have spaces, values can
        tval = tline.replace(tkey + " ", "")
#        tval = tline.split(' ')[1]
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

#### Don't alter this, this loads in ENV variables

    def load_env(self, evars):
        for v in evars:
            ev = self.env_pre + v.upper()
            if self.debug:
                print("Trying to load: %s" % ev)
            if ev in os.environ:
                tvar = os.environ[ev]
                if self.debug:
                    print("Loaded %s as %s" % (ev, tvar))
                self.opts[v][0] = tvar
            else:
                if self.debug:
                    print("Could not load %s" % ev)

