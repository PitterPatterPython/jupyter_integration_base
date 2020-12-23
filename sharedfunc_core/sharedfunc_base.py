#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
from collections import OrderedDict
from copy import deepcopy
import importlib

from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Javascript, FileLink, FileLinks, Image

# Widgets
from ipywidgets import GridspecLayout, widgets


@magics_class
class Sharedfunc(Magics):
    # Static Variables
    ipy = None              # IPython variable for updating and interacting with the User's notebook
    debug = False           # Enable debug mode
    mods = {}


    magic_name = "funcs"
    name_str = "sharedfunc"
    env_pre = "JUPYTER_"

    # Variables Dictionary
    max_full_results  = 1 # When searching, if your results are above this number it only returns the function name and keywords, otherwise it returns full description

    evars = []
    modevars = ["_url_"]

    gflat = {}

#    modgitver = "mymod@https://raw.githubusercontent.com/JohnOmernik/sharedmod/main/mymod/_funcdocs.py"

 #   JUPYTER_SHAREDFUNC_URL_MM="mymod@https://raw.githubusercontent.com/JohnOmernik/sharedmod/main/mymod/_funcdocs.py"

    # These are the variables in the opts dict that allowed to be set by the user. These are specific to this custom integration and are joined
    # with the base_allowed_set_opts from the integration base

    # These are the variables in the opts dict that allowed to be set by the user. These are specific to this custom integration and are joined
    # with the base_allowed_set_opts from the integration base

    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first. 
    # This is because they are designed to be self documenting. 
    # Each option item is actually a list of two length. 
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description. 

    dg = None # The main display grid


    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables. 
    def __init__(self, shell, debug=False, *args, **kwargs):
        self.debug = debug
        super(Sharedfunc, self).__init__(shell)
        self.ipy = get_ipython()
        self.load_env(self.evars)

        for m in self.mods:
            mloaded = False
            load_error = ""
            try:
                tmod = importlib.import_module(self.mods[m]['realname'])
                mloaded = True
            except Exception as e:
                str_err = str(e)
                load_error += "Module import failed: %s\n" % str_err
                # ----> This is where we should import it into the notebook kernel <--------
            if mloaded:
                try:
                    self.ipy.ex("import %s as %s" % (self.mods[m]['realname'], m))
                except Exception as e:
                    str_err = str(e)
                    load_error += "Error loading module %s as %s into kernel\n" % (self.mods[m]['realname'], m)

                try:
                    tflat = None
                    self.mods[m]['import_ver'] = tmod.__version__
                    self.mods[m]['funcdict'] = tmod.funcdict
                    tflat = self.flatfuncs(tmod.funcdict['modroot'], m)
                    self.mods[m]['flat'] = tflat
                    self.gflat.update(tflat)
                    self.mods[m]['imported'] = True
                except Exception as e:
                    str_err = str(e)
                    load_error += "Module import success - No Defined __version__ or fuctdict: %s\n" % str_err
            self.mods[m]['import_msg'] = load_error


    def retScope(self, sIn):
        lIn = sIn.lower().strip()
        if self.debug:
            print("sIn: %s - lIn: %s" % (sIn, lIn))
        aScope = [["name", "fullname"],["fullname", "fullname"], ["description", "description"], ["desc", "description"],
                  ["keywords", "keywords"], ["kw", "keywords"], ["authors", "authors"], ["author", "authors"]
                 ]
        dScope = {"fullname": False, "description": False, "keywords": False, "authors": False}
        for a in aScope:
            if lIn == "":
                if self.debug:
                    print("Setting %s to True" % a[1])
                dScope[a[1]] = True
            elif lIn.find(a[0]) >= 0:
                dScope[a[1]] = True
        return dScope

    def searchFuncs(self, iTerm, iScope=""):
    # Scope can be search
        ff = self.gflat
        lTerm = iTerm.lower().strip()
        sScope = self.retScope(iScope)
        if self.debug:
            print("Scope: %s" % sScope)
        sResults = {}
        scope_cnt = len([i for i in sScope.keys() if sScope[i]])
        if self.debug:
            print("Scope Count: %s" % scope_cnt)
        for f in ff:
            for s in sScope.keys():
                if sScope[s]:
                    if s in ['fullname', 'description', 'usage']:
                        if ff[f][s].lower().find(lTerm) >= 0: # Use lterm for searching text
                            if s in sResults:
                                sResults[s] += [ff[f]['fullname']]
                            else:
                                sResults[s] = [ff[f]['fullname']]
                    else:
                        if iTerm in ff[f][s]: # Exact match on Authors and keywords
                            if s in sResults:
                                sResults[s] += [ff[f]['fullname']]
                            else:
                                sResults[s] = [ff[f]['fullname']]
        sScore = {}
        for r in sResults:
            for f in sResults[r]:
                if f not in sScore:
                    sScore[f] = [1, 1/scope_cnt]
                else:
                    sScore[f][0] += 1
                    sScore[f][1] = sScore[f][0] / scope_cnt
        return sScore


    def handleSearch(self, c, l):
        if self.debug:
            print("Line: %s" % l)
            print("Cell: %s" % c)
        myScore = self.searchFuncs(l, c)
        sortedScore = dict(sorted(myScore.items(), key=lambda item: item[1][1], reverse=True))
        pFull = True
        if len(sortedScore.keys()) > self.max_full_results:
            pFull = False
        for x in sortedScore.keys():
            print("%s - Score: %s" % (x, sortedScore[x][1]))
            if pFull:
                self.displayFunc(x)


    def flatfuncs(self, troot, basename):
        tret = {}
        for f in troot['funcs']:
            n = f['name']
            tn = basename + "." + n
            tret[tn] = f
            tret[tn]['fullname'] = tn
        for c in troot['children'].keys():
            tb = basename + "." + c
            tret.update(self.flatfuncs(troot['children'][c], tb))
        return tret

    def remove_ev_quotes(self, val):
        retval = ""
        if val[0] == '"' and val[-1] == '"':
            retval = val[1:-1]
        elif val[0] == "'" and val[-1] == "'":
            retval = val[1:-1]
        else:
            retval = val
        return retval

    def fill_mods(self, mod_name, url):
        mod_realname = url.split("@")[0]
        mod_giturl = url.split("@")[1]

        self.mods[mod_name] = {"realname": mod_realname , "url": mod_giturl, "url_ver": None, "imported": False, "import_ver": None, "import_msg": "", "funcdict": None}


    def displayFunc(self, fname):

        if fname not in self.gflat:
            print("Function %s does not exist in loaded shared functions")
        else:
            f = self.gflat[fname]
            modalias = fname.split(".")[0]
            modname = self.mods[modalias]['realname']

            print("")
            print("Function: %s" % fname)
            print("----------------------------------------------------------")
            print("Source: import %s as %s" % (modname, modalias))
            print("Author: %s" % f['authors'])
            print("Keywords: %s" % f['keywords'])
            print("")
            print("Description: %s" % f['description'])
            print("")
            print("Arguments: ")
            for a in f['args']:
                print("\t%s - %s - %s" % (a[0], a[1], a[2]))
                print("\t\t%s" % a[3])
            print("")
            print("Returns (in order of return): ")
            for r in f['returns']:
                print("\t%s - %s"  % (r[0], r[1]))
            print("")
            print("Usage:")
            print(f['usage'])
            print("")

    def listFuncs(self, mod):
        if mod == "":
            tmod = "None"
        else:
            tmod = mod

        print("Defined, documented shared functions (module filter: %s)" % tmod)
        print("")
        for m in self.gflat.keys():
            if tmod == "None" or m.find(tmod) == 0:
                print(m)

    def load_env(self, evars):

        for v in [self.name_str + i for i in self.modevars] + evars:
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
                        if base_var == "url":
                            self.fill_mods(instance, tval)
                        else:
                            self.instances[instance][base_var] = tval

    def listmods(self):
        print("")
        print("Modules defined for documentation:")
        print("----------------------------------")

        for m in self.mods.keys():
            cmod = self.mods[m]
            print("Module %s requested to be loade as %s" % (cmod['realname'], m))
            print("\tImported: %s" % cmod['imported'])
            print("\tImport Message: %s" % cmod['import_msg'])
            print("\tImport Version: %s" % cmod['import_ver'])
            print("\tgit url: %s" % cmod['url'])
            print("\tgit version: %s" % cmod['url_ver'])
            print("")
            print("")


    def showActiveImports(self, line):
        bShowAll = False
        outcell = ""
        if line.replace("imports ", "").strip() == "all":
            bShowAll = True
        for m in self.mods:
            asname = m
            realname = self.mods[m]['realname']
            imported = self.mods[m]['imported']
            if imported or bShowAll:
                outcell += "import %s as %s\n" % (realname, m)
        if not bShowAll:
            print("Only successfully imported modules showing")
        else:
            print("All requested modules show, even if they did not successfully import")
        self.ipy.set_next_input(outcell)


    def customHelp(self):
        m = "%" + self.magic_name
        mq = "%" + m

        print("jupyter integrations has a (beta) shared functions doc interface that allows you to use the magic function %s and %s to help provide in notebook documentation for shared functions" % (m, mq))
        print("")
        print("Documentation has two main modes %s and %s" % (m, mq))
        print("%s is for interacting with specific parts of the doc help system and narrowing scope of %s queries" % (m, mq))
        print("%s is for running searches and obtaining results back from shared functions" % (mq))
        print("")
        print("%s functions available" % m)
        print("###############################################################################################")
        print("")
        print("{: <30} {: <80}".format(*[m, "This help screen"]))
        print("{: <30} {: <80}".format(*[m + " help", "Same as %s (prints this help screen)" % m]))
        print("{: <30} {: <80}".format(*[m + " debug", "Sets an internal debug variable to True (False by default) to see more verbose info about connections"]))
        print("{: <30} {: <80}".format(*[m + " mods", "List the requested modules, and their relavent information including import success"]))
        print("{: <30} {: <80}".format(*[m + " imports", "Show the actual import lines (in the next cell) for the successfully imported modules"]))
        print("{: <30} {: <80}".format(*[m + " list", "Show all documented functions handled by shared funcs"]))
        print("{: <30} {: <80}".format(*[m + " list <modname>", "Show all documented fucnctions in the <modname> module. (This is the alias)"]))
        print("{: <30} {: <80}".format(*[m + " display <funcname>", "Show the documentation for the <funcname> function as formatted in list"]))
        print("{: <30} {: <80}".format(*[m + " maxfull <number>", "The maximum number of search results to show the full function description (defaults to 1)"]))
        print("")
        print("%s usage available" % mq)
        print("###############################################################################################")
        print("%s is used to run searches across the scope provided.  Scope is provided on the same line as %s and the search terms on the next line" % (mq, mq))
        print("")
        print("Examples:")
        print("Search for any functions related to geoip")
        print("%s functions")
        print("geoip")
        print("")
        print("Search for any functions in the sharedsec module for active directory functions")
        print("%s functions sharedsec")
        print("active directory")
        print("")

    def setMaxFull(self, l):
        bFail = False
        try:
            new_max_full_results = int(l.replace("maxfull", "").strip())
            if new_max_full_results >= 0:
                print("Updated max_full_results from %s to %s" % (self.max_full_results, new_max_full_results))
                self.max_full_results = new_max_full_results
            else:
                bFail = True
        except:
            bFail = True
        if bFail == True:
            print("Unable to set maxfull results - Must pass an integer >= 0")
            print("Current Setting: %s"  % self.max_full_results)


        

  # This is the magic name.
    @line_cell_magic
    def funcs(self, line, cell=None):
        l_cell = None
        l_line = line.strip().lower()
        if cell is not None:
            l_cell = cell.strip().lower()

        if l_cell is None: # Line only magic submitted
            if (l_line == "") or l_line.find("help") == 0:
                self.customHelp()
            elif l_line.find("debug") == 0:
                print("Setting Debug to %s - Old Setting %s" % (not self.debug, self.debug))
                self.debug = not self.debug
            elif l_line.find("mods") == 0:
                self.listmods()
            elif l_line.find("list") == 0:
                self.listFuncs(l_line.replace("list", "").strip())
            elif l_line.find("imports") == 0:
                self.showActiveImports(l_line)
            elif l_line.find("display") == 0:
                self.displayFunc(l_line.replace("display", "").strip())
            elif l_line.find("maxfull") == 0:
                self.setMaxFull(l_line)
            else:
                print("line: %s" % l_line)
        else: # This is a cell (or a cell + line) call
            self.handleSearch(line, cell)

