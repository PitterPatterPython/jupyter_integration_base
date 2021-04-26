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

from IPython.display import display_html, display, Markdown, Javascript, FileLink, FileLinks, Image
import ipywidgets as widgets

import jupyter_integrations_utility as jiu

# nameing code
import traceback, threading, time
# end naming code

class InstanceCreationError(Exception):
    pass



#@magics_class
class Integration(Magics):
    # Static Variables
    ipy = None              # IPython variable for updating and interacting with the User's notebook
    instances = {}          # Instances 

#    instance['name'] = {"url": "source://user@host:port?option1=1&option2=2", connected: False} 
    global_evars = ['proxy_scheme', 'proxy_user', 'proxy_host', 'proxy_port'] # These are the ENV variables we check with. We upper() these and then prepend env_pre. so proxy_user would check the ENV variable JUPYTER_PROXY_HOST and let set that in opts['proxy_host']

    session = None          # Session if ingeration uses it. Most data sets have a concept of a session object. An API might use a requests session, a mysql might use a mysql object. Just put it here. If it's not used, no big deal.  This could also be a cursor

    connection = None       # This is a connection object. Separate from a cursor or session it only handles connecting, then the session/cursor stuff is in session. 
    connected = False       # Is the integration connected? This is a simple True/False 
    name_str = ""           # This is the name of the integraton, and will be prepended with % for the magic, used in variables, uppered() for ENV variables etc. 
    magic_name = ""
    connect_pass = ""       # Connection password is special as we don't want it displayed, so it's a core component
    proxy_pass = None         # If a proxy is required, we need a place for a password. It can't be in the opts cause it would be displayed. 
    debug = False           # Enable debug mode
    env_pre = "JUPYTER_"    #  Probably should allow this to be set by the user at some point. If sending in data through a ENV variable this is the prefix




    # These are the variables we allow users to set no matter the inegration (we should allow this to be a customization)

    base_allowed_set_opts = [
                              'default_instance_name',
                              'm_replace_a0_20', 'm_replace_crlf_lf'
                            ]



    # Variables Dictionary
    opts = {}
    req_addons = ['helloworld', 'display', 'persist', 'profile', 'sharedfunc', 'vis']
 #   integration_evars = ['_conn_url_'] # These are per integration env vars checked. They will have self.name_str prepended to them for each integration"
    integration_evars = ['_conn_url_'] + ['_' + i for i in global_evars] + ['_' + i + '_' for i in global_evars]


    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first.
    # This is because they are designed to be self documenting.
    # Each option item is actually a list of two length.
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description.

    # Pandas Variables
    opts['default_instance_name'] = ['default', "The instance name used as a default"]
 #   opts['pd_display_grid'] = ['na', "This is legacy, and needs to be removed once all integrations that reference it stop using it - It is not used"]

    opts['m_replace_a0_20'] = [False, 'Replace hex(a0) with space (hex(20)) on magic submission - On lines and cells']
    opts['m_replace_crlf_lf'] = [True, 'Replace crlf with lf (convert windows to unix line endings) on magic submission - Only on cells, not lines']



    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables. 






    def __init__(self, shell, debug=False, *args, **kwargs):
        self.debug = debug
        super(Integration, self).__init__(shell)
        self.ipy = shell
        self.load_env(self.global_evars)
        self.check_req_addons()
        if self.magic_name == "":
            self.magic_name = self.name_str
        if 'jupyter_loaded_integrations' not in shell.user_ns:
            shell.user_ns['jupyter_loaded_integrations'] = [self.name_str]
        else:
            shell.user_ns['jupyter_loaded_integrations'].append(self.name_str)

        # Begin Name Code
        for frame, line in traceback.walk_stack(None):
            varnames = frame.f_code.co_varnames
            if varnames == ():
                break
            if frame.f_locals[varnames[0]] not in (self, self.__class__):
                break
                # if the frame is inside a method of this instance,
                # the first argument usually contains either the instance or
                #  its class
                # we want to find the first frame, where this is not the case
        else:
            raise InstanceCreationError("No suitable outer frame found.")
        self._outer_frame = frame
        self.creation_module = frame.f_globals["__name__"]
        self.creation_file, self.creation_line, self.creation_function, \
            self.creation_text = \
            traceback.extract_stack(frame, 1)[0]
        self.creation_name = self.creation_text.split("=")[0].strip()
        threading.Thread(target=self._check_existence_after_creation).start()


    def _check_existence_after_creation(self):
        while self._outer_frame.f_lineno == self.creation_line:
            time.sleep(0.01)
        # this is executed as soon as the line number changes
        # now we can be sure the instance was actually created
        error = InstanceCreationError(
                "\nCreation name not found in creation frame.\ncreation_file: "
                "%s \ncreation_line: %s \ncreation_text: %s\ncreation_name ("
                "might be wrong): %s" % (
                    self.creation_file, self.creation_line, self.creation_text,
                    self.creation_name))
        nameparts = self.creation_name.split(".")
        try:
            var = self._outer_frame.f_locals[nameparts[0]]
        except KeyError:
            raise error
        finally:
            del self._outer_frame
        # make sure we have no permament inter frame reference
        # which could hinder garbage collection
        try:
            for name in nameparts[1:]: var = getattr(var, name)
        except AttributeError:
            raise error
        if var is not self: raise error

    def print_creation_info(self):
        print(self.creation_name, self.creation_module, self.creation_function,
                self.creation_line, self.creation_text, sep=", ")

#### End Name code

    def check_req_addons(self):
        for addon in self.req_addons:
            chk = addon + "_var"
            if chk not in self.ipy.user_ns:
                if self.debug:
                    print("%s not found in user_ns - Running" % chk)
                objname = addon.capitalize()
                corename = addon + "_core"
                varobjname = "my" + addon
                runcode = "from %s import %s\n%s = %s(ipy, debug=%s)\nipy.register_magics(%s)\n" % (corename, objname, varobjname, objname, str(self.debug), varobjname)
                if self.debug:
                    print(runcode)
                res = self.ipy.run_cell(runcode)
            else:
                if self.debug:
                    print("%s found in user_ns - Not starting" % chk)
    def retProxy(self, instance=None):
        proxystr = self.get_proxy_str(instance)
        if self.debug:
           print("Proxy String: %s" % proxystr)
        prox_pass = self.get_proxy_pass(proxystr, instance)
        proxurl = proxystr.replace("@", ":" + prox_pass + "@")
        proxies = {'http': proxurl, 'https': proxurl}
        return proxies

    def get_proxy_str(self, instance=None):
        phost = self.get_global_eval("proxy_host", instance)
        puser = self.get_global_eval("proxy_user", instance)
        pscheme = self.get_global_eval("proxy_scheme", instance)
        pport = self.get_global_eval("proxy_port", instance)
        purl = "%s://%s@%s:%s" % (pscheme, puser, phost, pport)
        return purl

    def get_proxy_pass(self, proxy_str, instance=None):
        ret_val = None
        if instance is not None:
            if 'proxy_pass' in self.instances[instance]:
                ret_val = self.instances[instance]['proxy_pass']
                if self.debug:
                    print("Proxy pass set at instance level")
        if ret_val is None:
            int_var = self.name_str + "_proxy_pass"
            try:
                ret_val = eval("self." + int_var)
                if self.debug:
                    print("Proxy pass set at the integration level")
            except:
                pass
        if ret_val is None:
            try:
                ret_val = eval("self.proxy_pass")
                if self.debug:
                    print("Proxy pass set at the global level")
            except:
                pass
        if ret_val is None:
            # If we didn't find a password, than we will set it and it gets set by default at the integration level.
            # The reason is is it's a good place, and there are ways to set at the instance level if needed (or should be)
            print("Proxy password for use with %s integration not set at any level - Requesting password" % self.name_str)
            ret_val = self.set_proxy_pass(proxy_str, 'integration', instance)

        return ret_val

    def set_proxy_pass(self, proxy_str, level, instance=None):
        # We set the password based on the level, but we also return it if needed.
        myname = self.name_str
        ret_val = None
        allowed_levels = ['integration', 'instance']
        if level not in allowed_levels:
            print("Requested level: %s not in allowed_levels: %s" % (level, allowed_levels))
            print("Password not set")
        elif instance is None and level == "instance":
            print("Requested instance password set with no instance provided")
        else:
            print("Please enter %s level password for proxy: %s (Instance: %s)" % (level, proxy_str, instance))
            print("")
            tproxpass = ""
            self.ipy.ex("from getpass import getpass\ntproxpass = getpass(prompt='Proxy Password: ')")
            tproxpass = self.ipy.user_ns['tproxpass']
            if level == "integration":
                exec('self.' + self.name_str + '_proxy_pass = tproxpass')
            elif level == "global":
                exec('self.proxy_pass = tproxpass')
            else:
                self.instances[instance]['proxy_pass'] = tproxpass
            ret_val = tproxpass
            self.ipy.user_ns['tproxpass'] = ""
            tproxpass = ""
        return ret_val

##### connect should not need to be overwritten by custom integration
    def connect(self, instance=None, prompt=False):
        if self.debug:
            print("Connect function - Instance: %s - Prompt: %s - " % (instance, prompt))


        if instance is None:
            instance = self.opts[self.name_str + "_conn_default"][0]
        instance = instance.strip().replace('"', '')


        if instance not in self.instances.keys() or prompt == True:
            print("Instance %s not found or prompt requested, adding and connecting" % instance)
            print("")
            print("Please enter the conn_url for the %s instance: " % instance)
            print("Format: <scheme>://<user>@<host>:<port>?<option1>=<option1_val>&<option2>=<option2_val>")
            tconn_url = input("conn_url for %s instance: " % instance)
            self.fill_instance(instance, tconn_url)
            self.parse_instances(parse_inst=instance)


        req_pass = self.req_password(instance)
        req_user = self.req_username(instance)
        req_otp = self.req_otp(instance)
        if self.debug:
            print("req_user: %s - req_pass: %s" % (req_user, req_pass))



        inst = self.instances[instance]

        if inst['connected'] == False:
            if (prompt == True or inst['user'] == "") and req_user == True:
                print("User not specified in env %s%s_CONN_URL_%s or user override requested" % (self.env_pre, self.name_str.upper(), instance.upper()))
                tuser = input("Please type user name if desired: ")
                inst['user'] = tuser
            if inst['user'] is None or inst['user'] == "":
                myuser = "none"
            else:
                myuser = inst['user']
            jiu.displayMD("Connecting to instance **%s** as **%s**\n\n" % (instance, myuser))

            if ((inst['connect_pass'] is None and self.instances[self.opts[self.name_str + "_conn_default"][0]]['connect_pass'] is None) or prompt == True) and req_pass == True:
                print("Please enter the password for the %s instance that you wish to connect with:" % instance)
                tpass = ""
                self.ipy.ex("from getpass import getpass\ntpass = getpass(prompt='Connection Password: ')")
                tpass = self.ipy.user_ns['tpass']

                inst['connect_pass'] = tpass
                self.ipy.user_ns['tpass'] = ""


            # Should OTP be hidden? I do not believe so, but could be argued
            # Also, unlike password, we request otp every time we need to.
            if req_otp == True:
                print("Please enter the One Time Password (OTP) for the %s instance you wish to connect with." % instance)
                totp = ""
                totp = input("Please enter OTP: ")
                inst['connect_otp'] = totp
                totp = ""

            result = self.customAuth(instance)

            if result == 0:
                inst["connected"] = True
                jiu.displayMD("**%s - Connected** - %s\n\n" % (self.name_str.capitalize(), inst['conn_url']))
            else:
                inst['connect_pass'] = None
                jiu.displayMD("## Connection Error\n--------\nConnection Error Code: %s\n\n" % result)

        elif inst['connected'] == True:
            jiu.displayMD("%s instance %s is already connected." % (self.name_str.capitalize(), instance))
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

    def req_otp(self, instance):
        # This is a simple function that can be overwritten by custom integrations.
        # The default (this function) says "no, it does NOT require a One Time Password (OTP)"
        # however, if a customer integration has an instance parameter where a certain instance requires it, it can be set to prompt by overriding this
        retval = False
        return retval


##### This is the base integration for line magic (single %), it handles the common items, and if the magic isn't common, it sends back to the custom integration to handle
    def handleLine(self, line):
        if self.opts['m_replace_a0_20'][0] == True:
            line = line.replace("\xa0", " ")

        bMischiefManaged = False
        # Handle all common line items or return back to the custom integration
        if line == "" or line.lower().find("help") == 0:
            bMischiefManaged = True
            jiu.displayMD(self.retHelp())
        elif line.lower() == "status":
            bMischiefManaged = True
            jiu.displayMD(self.retStatus())
        elif line.lower() == "progquery":
            self.displayProgQueryHelp()
            bMischiefManaged = True
        elif line.lower() == "debug":
            print("Toggling Debug from %s to %s" % (self.debug, not self.debug))
            self.debug = not self.debug
            bMischiefManaged = True
        elif line.lower() == "instances":
            bMischiefManaged = True
            jiu.displayMD(self.retInstances())
        elif line.lower().find("setpass") == 0:
            bMischiefManaged = True
            self.setPass(line)
        elif line.lower().find("setproxypass") == 0:
            bMischiefManaged = True
            t = self.set_proxy_pass("%s Integration Proxy Pass" % self.name_str, "integration")
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



##### handleCell should NOT need to be overwritten, however, I guess it could be
    def handleCell(self, cell, line=None):
        bPersist = False
        sPersist = ""
        tPersist = ""
        instance = ""
        integration = self.name_str
        if line is None or line == "":
            instance = self.opts[self.name_str + "_conn_default"][0]
            bPersist = False
        else:
            arline = line.split(" ")
            if len(arline) == 1:
                tline = arline[0].strip()
                if tline.find("p:") == 0:
                    instance = self.opts[self.name_str + "_conn_default"][0]
                    bPersist = True
                    sPersist = tline.replace("p:", "")
                else:
                    instance = tline
                    bPersist = False
            else:
                if arline[0].strip().find("p:") == 0:
                    tPersist = line
                    instance = self.opts[self.name_str + "_conn_default"][0]
                else:
                    instance = arline[0].strip()
                    tPersist = line.replace(instance, "").strip()
                if tPersist.find("p:") >= 0:
                    sPersist = tPersist.replace("p:", "").strip()
                    bPersist = True
                else:
                    print("Unknown line data beyond instance name, ignoring")
        if instance in self.instances:
            

            if self.opts['m_replace_crlf_lf'][0] == True:
                cell = cell.replace("\r\n", "\n")
            if self.opts['m_replace_a0_20'][0] == True:
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
                    if bPersist:
                        if "persist_var" in self.ipy.user_ns:
                            persisted_id = self.ipy.user_ns[self.ipy.user_ns["persist_var"]].persistData(result_df, notes=sPersist, integration=integration, instance=instance, query=cell, confirm=True)
                            print("Query Persisted with ID: %s" % persisted_id)
                        else:
                            print("persist_var is not found in the ipy user name space, you will need to instantiate the persistance core for this to work")
                            print("Warning: Your query was NOT persisted")
                    display_var = self.ipy.user_ns['display_var']
                    self.ipy.user_ns[display_var].displayDF(result_df, instance, qtime)
            else:
                print(self.name_str.capitalize() + " instance " + instance + " is not connected: Please see help at %" + self.name_str)
        else:
            print("Provided Instance: %s not found in defined instances" % instance)

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
####


    def retHelp(self):
        n = self.name_str
        mn = self.magic_name
        m = "%" + mn
        mq = "%" + m
        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"


        out = ""
        out += "# %s - Jupyter Integrations Datasource Integration Help System\n" % m
        out += "------------------\n"
        out += self.retCustomDesc() + "\n\n"
        out += "## %s line magic \n" % (m)
        out += "---------------------\n"
        out += "### Standard Integration Line Magics\n"
        out += table_header
        out += "| %s | This Help Screen |\n" % m
        out += "| %s | Display help on programmatic queries with integrations |\n" % (m + " progquery")
        out += "| %s | Show the status of the %s addon, including variables used for config |\n" % (m + " status", m)
        out += "| %s | Sets the internal debug flag - Used to see more verbose info on addon functionality |\n" % (m + " debug")
        out += "| %s | Sets a the 'variable' provided to the 'value' provided |\n" % (m + " set 'variable' 'value'")
        out += "| %s | Sets the proxy password at the integration level |\n" % (m + " setproxypass")
        out += "\n\n"
        out += "### Working with instances\n"
        out += table_header
        out += "| %s | Show defined instances and their status |\n" % (m + " instances")
        out += "| %s | Connect to (optional) 'instance' (uses default if ommited) with defined settings. Use alt to override url and user settings |\n" % (m + " connect 'instance' [alt]")
        out += "| %s | Disconnect from  (optional) <instance> (uses default if ommitted). |\n" % (m + " disconnect <instance>")
        out += "| %s | Set password for (optional) <instance> (uses default if ommitted). |\n" % (m + " setpass <instance>")
        out += "\n\n"
        out = self.customHelp(out)

        return out

    def retCustomDesc(self):
        return "Standard Datasource integration as part of Jupyter Integrations"


    def customHelp(self, curout):
        out = curout
        out += self.displayProgQueryHelp()
        return out





##### displayHelp should only be in base. It allows a global level of customization, and then calls the custom help in each integration that's unique
    def displayHelp(self):
        print("***** Jupyter Integrations Help System")
        print("")
        print("Required Addon Status:")
        print("{: <30} {: <30}".format(*["Addon", "Addon Loaded"]))
        for addon in self.req_addons:
            chk = addon + "_var"
            bFound = False
            if chk in self.ipy.user_ns:
                m = '%' + self.ipy.user_ns[self.ipy.user_ns[chk]].magic_name
                bFound = True
                print("{: <30} {: <30}".format(*[m, str(bFound)]))
        print("")
        self.customHelp()


    def displayProgQueryHelp(self):

        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m

        myname = self.creation_name

        print("As an alternative to interactive queries with magic functions, Jupyter Integrations also has the ability to perform programmatic queries after you connect")
        print("This feature is designed to allow an analyst to connect using the %integration connect magic,and then write python code that can build queries based on results")
        print("")
        print("Note: If you want to script the whole operation, you should just be writing a python script at this point and will have to handle secrets")
        print("")
        print("Here is normal query:")
        print("")
        print("%s default\nselect * from table" % (mq))
        print("")
        print("This query is run on the default instace for the %s integration " % n)
        print("")
        print("To make this programatic:")
        print("")
        print("results_df, query_time, result_str = %s.runQuery('select * from table', 'default')" % myname)
        print("")
        print("The results_df variable will have the results in a dataframe. (you can display through %s.displayDF(results_df))" % myname)
        print("The query_time variable will have the time it took to run the query")
        print("The result_str variable will have a status of the results, if it starts with Success, it worked, if Failure, (with more info) it did not)")
        print("")



    # displayIntegrationHelp is a helperfunction only. Not a class function Consider moving to utlities
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
        print("{: <30} {: <80}".format(*[m + " progquery", "Display help on programmetic queries with integrations"]))
        print("{: <30} {: <80}".format(*[m + " display <dataframe>", "Use the current display settings of the %s integration and display the dataframe provided (regardless of source)" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " status", "Print the status of the %s connection and variables used for output" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " instances", "Print the status of the %s instances currently defined" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " setpass <instance>", "Sets the password for the specified instance (or conn_default instance if not defined) - Does not connect"]))
        print("{: <30} {: <80}".format(*[m + " setproxypass", "Sets the proxy password at an integration level"]))
        print("{: <30} {: <80}".format(*[m + " connect <instance>", "Initiate a connection to the %s cluster, if instance is not provided, defaults to conn_default" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " connect <instance> alt", "Initiate a connection to the %s cluster, and prompt for information. If instance is not provided, defaults to conn_default" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " disconnect <instance>", "Disconnect an active %s connection and reset connection variables. If instance is not provided, defaults to conn_default" % n.capitalize()]))
        print("{: <30} {: <80}".format(*[m + " set <instance> %variable% %value%", "Set the variable %variable% to the value %value% - Instance is optional - defaults to conn_default"]))
        print("{: <30} {: <80}".format(*[m + " debug", "Sets an internal debug variable to True (False by default) to see more verbose info about connections"]))

    # displayQueryHelp is a helperfunction only. Consider moving this to utilities.
    def retQueryHelp(self, q_examples=None):
        n = self.name_str
        mn = self.magic_name
        m = "%" + mn
        mq = "%" + m
        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = ""
        # Examples are [ instance line, query line, description]
        examples = []
        examples.append(["'instance'", "'Query in Native Language'", "Run A Query on the 'instance' (uses default if ommitted)"])
        if q_examples is not None:
            examples = examples + q_examples
        if self.debug:
            print(examples)
        out += "## Running Queries with %s\n" % (mq)
        out += "-----------------\n"
        out += "When running queries with %s, %s will be on the first line of your cell, with an optional 'instance' and the next line is the 'query' you wish to run.\n" % (mq, mq)
        out += "### Query Examples\n"
        out += "--------------------\n"
        out += table_header
        for ex in examples:
            line1 = mq + " " + ex[0]
            out += "| %s | %s |\n" % (line1.strip() + "<br>" + ex[1].strip(), ex[2].strip())
        out += "\n\n"
        out += "## Query Notes\n"
        out += "- If the number of results is less than the %display subsystem display_max_rows, results will be displayed directly after query\n"
        out += "- You may change the display_max_rows with `%display set display_max_rows 20000` to set to 20000 for example\n"
        out += "- All results, regardless of display, will be in a variable named prev_%s_<instance> where <instance> is the instance name. Example: `prev_%s_default`\n" % (mn, mn)
        out += "- prev_%s_<instance> is overwritten every time a successful query is run. If you wish to save, assign it to a new variable\n" % (mn)
        out += "\n\n"
        return out


    def retInstances(self):
        n = self.name_str
        mn = self.magic_name
        m = "%" + mn
        mq = "%" + m
        def_instance =  self.opts[self.name_str + "_conn_default"][0]

        out = ""
        out += "# %s instances\n" % n
        out += "---------------\n"
        out += "| default | instance | conn_url | connected | last_query | options |\n"
        out += "| ------- | -------- | -------- | --------- | ---------- | ------- |\n"
        for i in self.instances.keys():
            inst = self.instances[i]
            mydef = False
            if i == def_instance:
                mydef = True
            else:
                mydef = False
            out += "| %s | %s | %s | %s | %s | %s |\n" % (mydef, i, inst['conn_url'], inst['connected'], inst['last_query'], inst['options'])
        return out


#### retStatus should not be altered this should only exist in the base integration
    def retStatus(self):
        n = self.name_str
        mn = self.magic_name
        m = "%" + mn
        mq = "%" + m


        table_header = "| Variable | Value | Description |\n"
        table_header += "| -------- | ----- | ----------- |\n"

        out = ""
        out += "# Current State of %s Interface\n" % self.name_str
        out += "---------------------\n"
        out += "\n"
        out += "## Integration Base Properties\n"
        out += table_header
        out += "| debug | %s | Sets verbose out with %s debug |\n" % (self.debug, m)

        for k, v in self.opts.items():
            if k.find("m_") == 0:
                desc = v[1]
                if v[0] is None:
                    val = "None"
                else:
                    val = v[0]
                out += "| %s | %s | %s |\n" % (k, val, desc)

        out += "\n\n"
        out += "## %s Properties\n" % n
        out += table_header
        for k, v in self.opts.items():
            if k.find(self.name_str + "_") == 0:
                if v[0] is None:
                    val = "None"
                else:
                    val = str(v[0])
                desc = v[1]
                out += "| %s | %s | %s |\n" % (k, val, desc)

        out += "\n\n"
        out += self.customStatus()
        return out

    def customStatus(self):
        return ""

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
                oldval = self.instances[instance]['options'][tkey]
                self.instances[instance]['options'][tkey] = tval
                print("Set Instance Variable %s to %s - Previous Value: %s" % (tkey, tval, oldval))
            else:
                oldval = self.opts[tkey][0]
                try:
                    t = int(tval)
                except:
                    t = tval
                self.opts[tkey][0] = t
                print("Set Integration Variable %s to %s - Previous Value: %s" % (tkey, t, oldval))
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



    def get_global_eval(self, var, instance=None):
        # This function returns global variables by checking  in this order: instance, integration, global.
        # The lowest set item is returned. (i.e. if if instance is set, that is what is returned)
        # If isntance is none, then we start at the integration level
        retval = None
        if var in self.global_evars:
            if instance is not None:
                if var in self.instances[instance]:
                    retval = self.instances[instance][var]
                else:
                    if self.debug:
                        print("Instance %s provided, but var %s not found in instance vars" % (instance, var))
            if retval is None: # Even if the instance is here, if retval is still None, we didn't find the variables
                myname = self.name_str
                int_var = myname + "_" + var
                if int_var in self.opts:
                    retval = self.opts[int_var][0]
                else:
                    if self.debug:
                        print("%s not found in integration level variable %s" % (var, int_var))
                    if var in self.opts:
                        if self.debug:
                            print("Variable %s found at global - value: %s" % (var, self.opts[var][0]))
                        retval = self.opts[var][0]
                    else:
                        if self.debug:
                            print("Variable %s is in global_evars, but not set at the instace, integration, or global level" % var)
                # We have a integration level global:
        else:
            if self.debug:
                print("Varible requested: %s is not a global_evar: %s" % (var, self.global_evars))
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
                    bgev = False
                    for gev in self.global_evars:
                        if v.find(gev) >= 0:
                            if v == gev:
                                tset = [tvar, "Jupyter Global value for %s" % gev]
                                self.opts[v] = tset
                                bgev = True
                                break
                            elif v[0] != "_":
                                tset = [tvar, "Integration Global value for %s" % gev]
                                self.opts[v] = tset
                                bgev = True
                                break
                    if not bgev:
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
                            try:
                                self.instances[instance][base_var] = tval
                            except:
                                if self.debug:
                                    print("Could not set instace variable %s - Instance %s not created yet" % (base_var, instance))

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
