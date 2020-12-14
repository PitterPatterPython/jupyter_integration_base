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
    instances = {}          # Instances 

#    instance['name'] = {"url": "source://user@host:port?option1=1&option2=2", connected: False} 

    session = None          # Session if ingeration uses it. Most data sets have a concept of a session object. An API might use a requests session, a mysql might use a mysql object. Just put it here. If it's not used, no big deal.  This could also be a cursor
    
    connection = None       # This is a connection object. Separate from a cursor or session it only handles connecting, then the session/cursor stuff is in session. 
    connected = False       # Is the integration connected? This is a simple True/False 
    name_str = ""           # This is the name of the integraton, and will be prepended with % for the magic, used in variables, uppered() for ENV variables etc. 
    connect_pass = ""       # Connection password is special as we don't want it displayed, so it's a core component
    proxy_pass = ""         # If a proxy is required, we need a place for a password. It can't be in the opts cause it would be displayed. 
    debug = False           # Enable debug mode
    env_pre = "JUPYTER_"    #  Probably should allow this to be set by the user at some point. If sending in data through a ENV variable this is the prefix


    


    base_allowed_set_opts = ['qg_header_autofit', 'qg_header_pad', 'qg_colmin', 'qg_colmax', 'qg_text_factor', 'qg_autofit_cols', 'default_instance_name', 'pd_display.max_columns', 'pd_display.max_rows', 'pd_max_colwidth', 'pd_display_grid', 'pd_display_idx', 'q_replace_a0_20', 'q_remove_cr', 'qg_defaultColumnWidth', 'qg_maxVisibleRows', 'qg_minVisibleRows'] # These are the variables we allow users to set no matter the inegration (we should allow this to be a customization)

    pd_set_vars = ['pd_display.max_columns', 'pd_display.max_rows', 'pd_max_colwidth', 'pd_display_grid'] # These are a list of the custom pandas items that update a pandas object


    # Variables Dictionary
    opts = {}
    integration_evars = ['_conn_url_'] # These are per integration env vars checked. They will have self.name_str prepended to them for each integration"

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
    opts['pd_display.max_rows'] = [10000, 'Number of Max Rows']
    opts['default_instance_name'] = ['default', "The instance name used as a default"]
    opts['pd_display.max_columns'] = [None, 'Max Columns']
    opts['pd_display_grid'] = ["html", 'How pandas DF should be displayed']
    opts['qg_defaultColumnWidth'] = [200, 'The default column width when using qgrid']
    opts['qg_maxVisibleRows'] = [25, 'The default max number of rows visible in qgrid']
    opts['qg_minVisibleRows'] = [8, 'The default min number of rows visible in qgrid']
    opts['qg_colmin'] = [75, 'The minimum size a qgrid column will be']
    opts['qg_colmax'] = [750, 'The maximum size a qgrid column will be']
    opts['qg_text_factor'] = [8, 'The multiple of the str length to set the column to ']
    opts['qg_autofit_cols'] = [True, 'Do we try to auto fit the columns - Beta may take extra time']
    opts['qg_header_autofit'] = [True, 'Do we include the column header (column name) in the autofit calculations?']
    opts['qg_header_pad'] = [2, 'If qg_header_autofit is true, do we pad the column name to help make it more readable if this > 0 than it is the amount we pad']
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



##### connect should not need to be overwritten by custom integration
    def connect(self, instance=None, prompt=False):
        if self.debug:
            print("Connect function - Instance: %s - Prompt: %s - " % (instance, prompt))


        if instance is None:
            instance = self.opts[self.name_str + "_conn_default"][0]
        instance = instance.strip().replace('"', '')

        req_pass = self.req_password(instance)
        req_user = self.req_username(instance)

        if self.debug:
            print("req_user: %s - req_pass: %s" % (req_user, req_pass))

        if instance not in self.instances.keys() or prompt == True:
            print("Instance %s not found or prompt requested, adding and connecting" % instance)
            print("")
            print("Please enter the conn_url for the %s instance: " % instance)
            print("Format: <scheme>://<user>@<host>:<port>?<option1>=<option1_val>&<option2>=<option2_val>")
            tconn_url = input("conn_url for %s instance: " % instance)
            self.fill_instance(instance, tconn_url)
            self.parse_instances(parse_inst=instance)

        inst = self.instances[instance]

        if inst['connected'] == False:
            if (prompt == True or inst['user'] == "") and req_user == True:
                print("User not specified in env %s%s_CONN_URL_%s or user override requested" % (self.env_pre, self.name_str.upper(), instance.upper()))
                tuser = input("Please type user name if desired: ")
                inst['user'] = tuser
            print("Connecting as user %s" % inst['user'])
            print("")

            if ((inst['connect_pass'] is None and self.instances[self.opts[self.name_str + "_conn_default"][0]]['connect_pass'] is None) or prompt == True) and req_pass == True:
                print("Please enter the password for the %s instance that you wish to connect with:" % instance)
                tpass = ""
                self.ipy.ex("from getpass import getpass\ntpass = getpass(prompt='Connection Password: ')")
                tpass = self.ipy.user_ns['tpass']

                inst['connect_pass'] = tpass
                self.ipy.user_ns['tpass'] = ""

            result = self.customAuth(instance)

            if result == 0:
                inst["connected"] = True
                print("%s - %s Connected!" % (self.name_str.capitalize(), inst['conn_url']))
            else:
                print("Connection Error - Perhaps Bad Usename/Password?")

        elif inst['connected'] == True:
            print(self.name_str.capitalize() + " instance " + instance + " is already connected - Please type %" + self.name_str + " for help on what you can you do")

        if inst['connected'] != True:
            self.disconnect(instance=instance)




##### disconnect should not need to be overwritten by customer integration
    def disconnect(self, instance=None):
        if instance is None:
            instance = self.opts[self.name_str + "_conn_default"][0]

        if self.instances[instance]["connected"] == True:
            print("Disconnected %s Instance %s from %s" % (self.name_str.capitalize(), instance, self.instances[instance]['conn_url']))
        else:
            print("%s instance %s Not Currently Connected - Resetting All Variables" % (self.name_str.capitalize(), instance))
        
        self.customDisconnect(instance)
##### customDisconnect may be overwriittn by custom integrarion if more is needed to close the connection than this

    def customDisconnect(self, instance):
        self.instances[instance]['session'] = None
        self.instances[instance]['connected'] = False
        #self.instances[instance]['connect_pass'] = None # Should we clear the password when we disconnect? I am going to change this to no for now 


##### customAuth should be overwriittn by custom integrarion
    def customAuth(self, instance):
        # Return values:
        # 0  = Success
        # -1 = Generic Error
        # -2 = Exception from connection object
        # -3 = Instance not found
        self.session = None
        result = 0
        return result

##### validateQuery should be overwriittn by custom integrarion - without customer validateQuery, all queries are valid
    def validateQuery(self, query, instance):
        bRun = True
        bReRun = False
        return bRun

##### customQuery should be overwriittn by custom integrarion
    def customQuery(self, query, instance):
        return None, 0, "Failure - Not written"
    
##### Override this in an actual integration
    def customHelp(self):
        print("This would be custom help for the integration")


################################################################



    def req_password(self, instance):
        # This is a simple function that can be overwritten by custom integrations. 
        # The default (this function) says "yes, it requires a password"
        # however, if a customer integration has an instance parameter like Drill embedded or pyodbc use integrated security, it won't prompt for a password. 

        retval = True
        return retval

    def req_username(self, instance):
        # This is a simple function that can be overwritten by custom integrations. 
        # The default (this function) says "yes, it requires a username"
        # however, if a customer integration has an instance parameter like Drill embedded or pyodbc use integrated security, it won't prompt for a password. 

        retval = True
        return retval

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
        elif line.lower() == "instances":
            bMischiefManaged = True
            self.printInstances()
        elif line.lower().find("setpass") == 0:
            bMischiefManaged = True
            self.setPass(line)
        elif line.lower().strip().find("disconnect") == 0:
            myinstance = None
            instcheck = line.lower().strip().replace("disconnect", "").strip()
            if instcheck != "":
                if instcheck in self.instances.keys():
                    myinstance = instcheck
                else:
                    myinstance = None
            else:
                myinstance = None
            self.disconnect(instance=myinstance)
            bMischiefManaged = True
        elif line.lower().strip().find("connect") == 0: # Enhanced connect for instance check. 
            bprompt = False
            myinstance = None
            strline = line.lower().strip()
            instcheck = strline.replace("connect", "").strip()
            if instcheck.find(" alt") >= 0:
                bprompt = True
                inst = instcheck.replace("alt", "").strip()
            else:
                if instcheck != "": 
                    inst = instcheck
                else:
                    inst = None
            if self.debug:
                print("Search inst: %s" % inst)
            myinstance = inst
            self.connect(instance=myinstance, prompt=bprompt)
            bMischiefManaged = True
        elif line.lower().find('set ') == 0:
            self.setvar(line)
            bMischiefManaged = True
        else:
            pass
        return bMischiefManaged 


    def qgridDisplay(self, result_df, mycnt):

        # Determine the height of the qgrid (number of Visible Rows)
        def_max_rows = int(self.opts['qg_maxVisibleRows'][0])
        def_min_rows = int(self.opts['qg_maxVisibleRows'][0])
        max_rows = def_max_rows
        min_rows = def_min_rows
        if mycnt >= def_max_rows:
            max_rows = def_max_rows
            min_rows = def_min_rows
        elif mycnt + 2 <= def_max_rows:
            max_rows = def_max_rows
            min_rows = mycnt + 2

        mygridopts = {'forceFitColumns': False, 'maxVisibleRows': max_rows, 'minVisibleRows': min_rows, 'defaultColumnWidth': int(self.opts['qg_defaultColumnWidth'][0])}
        mycoldefs = {}

        # Determine Index width
        if self.opts['pd_display_idx'][0] == True:
            mydispidx = True
        else:
            mydispidx = False
            mycoldefs['index'] = { 'maxWidth': 0, 'minWidth': 0, 'width': 0 }

        # Handle Column Autofit
        if self.opts['qg_autofit_cols'][0] == True:
            maxColumnLenghts = []
            for col in range(len(result_df.columns)):
                maxColumnLenghts.append(max(result_df.iloc[:,col].astype(str).apply(len)))
            dict_size = dict(zip(result_df.columns.tolist(), maxColumnLenghts))
            text_factor = self.opts['qg_text_factor'][0]
            colmin = self.opts['qg_colmin'][0]
            colmax = self.opts['qg_colmax'][0]
            header_autofit = self.opts['qg_header_autofit'][0]
            header_pad = self.opts['qg_header_pad'][0]
            for k in dict_size.keys():
                if mydispidx or k != "index":
                    if header_autofit:
                        col_size = len(str(k)) + int(header_pad)
                        if dict_size[k] > col_size :
                            col_size = dict_size[k]
                    else:
                        col_size = dict_size[k]
                    mysize =  text_factor * col_size
                    if mysize < colmin:
                         mysize = colmin
                    if mysize > colmax:
                        mysize = colmax
                    mycoldefs[k] = {'width': mysize}


        # Display the QGrid
        display(qgrid.show_grid(result_df, grid_options=mygridopts, column_definitions=mycoldefs))


    def htmlDisplay(self, result_df, mycnt):
        display(HTML(result_df.to_html(index=self.opts['pd_display_idx'][0])))

# This can now be more easily extended with different display types
    def displayDF(self, result_df, instance=None, qtime=None):

        display_type = self.opts['pd_display_grid'][0]
        max_display_rows = self.opts['pd_display.max_rows'][0]
        if result_df is not None:
            mycnt = len(result_df)
        else:
            mycnt = 0

        if qtime is not None:
            print("%s Records from instance %s in Approx %s seconds" % (mycnt, instance, qtime))
            print("")
        else:
            print("%s Records Returned" % (mycnt))
            print("")

        if self.debug:
            print("Testing max_colwidth: %s" %  pd.get_option('max_colwidth'))

        if mycnt == 0:
            pass
        elif mycnt > max_display_rows:
            print("Number of results (%s) from instance %s greater than pd_display.max_rows(%s)" % (mycnt, instance, max_display_rows))
        else:
            if display_type == "qgrid":
                self.qgridDisplay(result_df, mycnt)
            elif display_type == "html":
                self.htmlDisplay(result_df, mycnt)
            else:
                print("%s display type not supported" % display_type)


##### handleCell should NOT need to be overwritten, however, I guess it could be
    def handleCell(self, cell, instance=None):
        if instance is None or instance == "":
            instance = self.opts[self.name_str + "_conn_default"][0]

        if self.opts['q_replace_crlf_lf'][0] == True:
            cell = cell.replace("\r\n", "\n")
        if self.opts['q_replace_a0_20'][0] == True:
            cell = cell.replace("\xa0", " ")
        if self.instances[instance]['connected'] == False:
            if self.instances[instance]['connect_pass'] is not None or self.instances[self.opts[self.name_str + "_conn_default"][0]]['connect_pass'] is not None or self.req_password(instance) == False:
                self.connect(instance)
        if self.instances[instance]['connected'] == True:
            result_df, qtime, status = self.runQuery(cell, instance)
            if status.find("Failure") == 0:
                print("Error from instance %s: %s" % (instance, status))
            elif status.find("Other: ") == 0:
                print("Non Query Results:\n" + status.replace("Other: ", ""))
            elif status.find("Success - No Results") == 0:
                print("No Results from instance: %s - returned in %s seconds" % (instance, qtime))
            elif status.find("ValidationError") == 0:
                print("Validation Error from instance %s" % instance)
            else:
                self.ipy.user_ns['prev_' + self.name_str + "_" + instance] = result_df
                self.displayDF(result_df, instance, qtime)
        else:
            print(self.name_str.capitalize() + " instance " + instance + " is not connected: Please see help at %" + self.name_str)


    def setPass(self, line):
        instance = line.replace("setpass", "").strip()
        if instance == "":
            instance = self.opts[self.name_str + "_conn_default"][0]
            print("setpass not passed an instance, using conn_default of %s" % instance)

        if self.req_password(instance):

            print("Please enter the password to save for the %s instance: " % instance)
            tpass = ""
            self.ipy.ex("from getpass import getpass\ntpass = getpass(prompt='Connection Password: ')")
            tpass = self.ipy.user_ns['tpass']
            self.instances[instance]['connect_pass'] = tpass
            self.ipy.user_ns['tpass'] = ""
            print("Password set for instance %s" % instance)
            tpass = ""
        else:
            print("Password not required for %s instance %s based on options" % (self.name_str.capitalize(), instance))

##### Leave runQuery in the base integration - it handles query timing, instead customize customerQuery in actual integration
    def runQuery(self, query, instance):

        mydf = None
        status = "-"
        starttime = int(time.time())
        run_query = self.validateQuery(query, instance)

        if run_query:
            if self.instances[instance]['connected'] == True:
                mydf, status = self.customQuery(query, instance)
            elif self.instances[instance]['connected'] == False and (self.instances[instance]['connect_pass'] is not None or self.instances[self.opts[self.name_str + "_conn_default"][0]]['connect_pass'] is not None):
                print("Instance %s - Not connected but password set at instance or at default - attempting connect before query" % instance)
                con_res = self.customAuth(instance)
                if con_res == 0:
                    mydf, status = self.customQuery(query, instance)
                else:
                    print("Could not auto connect instance %s - please connect and rerun query" % instance)
                    mydf = None
                    myjson = None
                    status = "%d instance %s Not Connected" % (self.name_str.capitalize(), instance)
            else:
                mydf = None
                status = "%d instance %s Not Connected" % (self.name_str.capitalize(), instance)
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

    def displayIntegrationHelp(self):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m
        
        print("jupyter_%s is a interface that allows you to use the magic function %s to interact with an %s installation." % (n, m, n.capitalize()))
        print("")
        print("jupyter_%s has two main modes %s and %s" % (n, m, mq))
        print("%s is for interacting with a %s installation, connecting, disconnecting, seeing status, etc" % (m, n.capitalize()))
        print("%s is for running queries and obtaining results back from the %s installation" % (mq, n.capitalize()))
        print("")
        print("%s functions available" % m)
        print("###############################################################################################")
        print("")
        print("{: <30} {: <80}".format(*[m, "This help screen"]))
        print("{: <30} {: <80}".format(*[m + " status", "Print the status of the %s connection and variables used for output" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " instances", "Print the status of the %s instances currently defined" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " setpass <instance>", "Sets the password for the specified instance (or conn_default instance if not defined) - Does not connect"]))
        print("{: <30} {: <80}".format(*[m + " connect <instance>", "Initiate a connection to the %s cluster, if instance is not provided, defaults to conn_default" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " connect <instance> alt", "Initiate a connection to the %s cluster, and prompt for information. If instance is not provided, defaults to conn_default" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " disconnect <instance>", "Disconnect an active %s connection and reset connection variables. If instance is not provided, defaults to conn_default" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " set <instance> %variable% %value%", "Set the variable %variable% to the value %value% - Instance is optional - defaults to conn_default"]))
        print("{: <30} {: <80}".format(*[m + " debug", "Sets an internal debug variable to True (False by default) to see more verbose info about connections"]))


    def displayQueryHelp(self, q_example):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m
        print("")
        print("Running queries with %s" % mq)
        print("###############################################################################################")
        print("")
        print("When running queries with %s, %s will be on the first line of your cell, with an optional instance and the next line is the query you wish to run. Example:" % (mq, mq))
        print("")
        print(mq)
        print(q_example)
        print("")
        print(mq + " myinstance")
        print(q_example)
        print("")
        print("Some query notes:")
        print("- If the number of results is less than pd_display.max_rows, then the results will be diplayed in your notebook")
        print("- You can change pd_display.max_rows with %s set pd_display.max_rows 2000" % m)
        print("- The results, regardless of being displayed will be placed in a Pandas Dataframe variable called prev_%s_<instance>" % n)
        print("- prev_%s_<instance> is overwritten every time a successful query is run. If you want to save results assign it to a new variable" % n)
        
    def printInstances(self):
        print("Current State of %s Instances:" % self.name_str.capitalize())
        print("")
        for i in self.instances.keys():
            print("")
            print("Instance: %s" % i)
            print("----------------------------------------------------------")
            for k in self.instances[i].keys():
                if k not in ['connect_pass']:
                    print("{: <30} {: <50}".format(*[k + ":", str(self.instances[i][k])]))

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
        ttest = tline.split(' ')[0] # Keys can't have spaces, values can
        instance = None
        if ttest in self.instances.keys():
            # This looks like an instance set var! 
            instance = ttest
            tkv = tline.replace(instace + " ", "")
            tkey = tkv.split(" ")[0]
            tval = tline.replace(instance + " " + tkey + " ", "")
        else:
            tkey = ttest
            tval = tline.replace(tkey + " ", "")
#        tval = tline.split(' ')[1]
        if tval == "False":
            tval = False
        if tval == "True":
            tval = True
        if tkey in allowed_opts:
            if instance is not None:
                self.instances[instance]['options'][tkey] = tval
            else:   
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

    def remove_ev_quotes(self, val):
        retval = ""
        if val[0] == '"' and val[-1] == '"': 
            retval = val[1:-1]
        elif val[0] == "'" and val[-1] == "'":
            retval = val[1:-1]
        else:
            retval = val
        return retval

    def load_env(self, evars):

        for v in [self.name_str + i for i in self.integration_evars] + evars:
            ev = self.env_pre + v.upper()
            if ev[-1] != "_": # Normal EV - put in options 
                if self.debug:
                    print("Trying to load: %s" % ev)
                if ev in os.environ:
                    tvar = self.remove_ev_quotes(os.environ[ev])
                    if self.debug:
                        print("Loaded %s as %s" % (ev, tvar))
                    self.opts[v][0] = tvar
                else:
                    if self.debug:
                        print("Could not load %s" % ev)
            elif ev[-1] == "_":  # This is a per instance variable - must default instances must be specified as default.
                base_var = v[0:-1].replace(self.name_str + "_", "")
                for e in os.environ:
                    if e.find(ev) == 0:
                        tval = self.remove_ev_quotes(os.environ[e])
                        instance = e.replace(ev, "").lower()
                        if base_var == "conn_url":
                            self.fill_instance(instance, tval)
                        else:
                            self.instances[instance][base_var] = tval

    def fill_instance(self, inst_name, conn_url):
        self.instances[inst_name] = {"conn_url": conn_url , "connected": False, "session": None, "connect_pass": None, "last_use": "", "last_query": ""}

    def parse_instances(self, parse_inst=None):
        if parse_inst is None: # Parse all instances
            parse_insts = list(self.instances.keys())
        else: # Parse a single instance
            parse_insts = [parse_inst]

        for i in parse_insts:
            i_url = self.instances[i]['conn_url']
            parse_success, parsed_dict = self.process_conn_url(i_url)
            if parse_success:
                for k in parsed_dict.keys():
                    self.instances[i][k] = parsed_dict[k]

    def checkvar(self, instance, var):
        retval = None
        if var in self.instances[instance]['options'].keys():
            retval = self.instances[instance]['options'][var]
        elif var in self.opts.keys():
            retval = self.opts[var][0]
        else:
            if self.debug:
                print("Unknown Variable requested: %s  - Returning None" % var)
        return retval



    def process_conn_url(self, myurl):
        ret_dict = {}
        options = {}
        parse_success = True
        ts = myurl.split("://")
        ret_dict['scheme'] = ts[0]
        try:
            tstr = ts[1]
        except:
            parse_success = False
            if self.debug:
                print("Could not parse initial scheme: %s" % url)
        if parse_success:
            ts1 = tstr.split("?")
            u_h_p = ts1[0]
            if len(ts1) > 1:
                t_o = ts1[1].split("&")
                for o in t_o:
                    kv = o.split("=")
                    try:
                        k = kv[0]
                        v = kv[1]
                    except:
                        parse_success = False
                        if self.debug:
                            print("Could not parse options: %s - Full URL: %s" % (ts1[1], myurl))
                    try:
                        v = int(v)
                    except:
                        pass
                    try:
                        options[k] = v
                    except:
                        pass
            ret_dict['options'] = options

            us = u_h_p.split("@")
            if len(us) == 1:
                ret_dict['user'] = ""
                hp = u_h_p
            elif len(us) == 2:
                ret_dict['user'] = us[0]
                hp = us[1]
            else:
                ret_dict['user'] = "@".join(us[0:-1])
                hp = us[-1]

            if parse_success:
                t_hp = hp.split(":")
                if len(t_hp) == 1:
                    ret_dict['host'] = t_hp[0]
                    ret_dict['port'] = None
                elif len(t_hp) == 2:
                    ret_dict['host'] = t_hp[0]
                    try:
                        ret_dict['port'] = int(t_hp[1])
                    except:
                        if self.debug:
                            print("Error converting %s to int for port" % t_hp[1])
                            parse_success = False
                else:
                    parse_success = False
                    if self.debug:
                        print("To many options (or not enough?) in host/port: %s - Full URL: %s" % (hp, myurl))
        if self.debug:
            print("url: %s" % myurl)
            print("Parse Success: %s" % parse_success)
            print("scheme: %s" % ret_dict['scheme'])
            print("user: %s" % ret_dict['user'])
            print("host: %s" % ret_dict['host'])
            print("port: %s" % ret_dict['port'])
            if len(ret_dict['options']) > 0:
                print("Options: ")
                for o in ret_dict['options']:
                    print("%s - %s" % (o, ret_dict['options'][o]))

        return parse_success, ret_dict
