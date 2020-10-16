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
class Doc(Magics):
    # Static Variables
    ipy = None              # IPython variable for updating and interacting with the User's notebook
    debug = False           # Enable debug mode
    documented_mods = []
    documented_funcs = {}
    # Variables Dictionary
    opts = {}
    
    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first. 
    # This is because they are designed to be self documenting. 
    # Each option item is actually a list of two length. 
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description. 

    dg = None # The main display grid


    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables. 
    def __init__(self, shell, debug=False, doc_mods=[], *args, **kwargs):
        self.debug = debug
        super(Doc, self).__init__(shell)
        self.ipy = get_ipython()
        bdoc = False
        for m in doc_mods:
            try:
                tmod = importlib.import_module(m)
                bdoc = True
            except:
                print("Import of module %s failed" % m)
            if bdoc:
                try:
                    bdoc = tmod.doc_funcs()
                except:
                    print("Import of %s worked, but no doc_funcs - no documentation checked")
                    bdoc = False            
            if bdoc:
                self.documented_mods.append(m)
                tfuncs = self.recursemod(m)
                tfuncs_dedupe = self.dedupe_funcs(tfuncs, m)
                self.documented_funcs[m] = tfuncs_dedupe

            else:
                if self.debug:
                    print("Did not load module: %s as it is not installed or didn't have the proper check functions" % m)


    def customHelp(self):
        m = "%doc"
        mq = "%" + m

        print("jupyter integrations has a (beta) doc interface that allows you to use the magic function %s and %s to help provide in notebook documentation for shared functions and data" % (m, mq))
        print("")
        print("Documentation has two main modes %s and %s" % (m, mq))
        print("%s is for interacting with specific parts of the doc help system and narrowing scope of %s queries" % (m, mq))
        print("%s is for running searches and obtaining results back from shared functions or datasets" % (mq))
        print("")
        print("%s functions available" % m)
        print("###############################################################################################")
        print("")
        print("{: <30} {: <80}".format(*[m, "This help screen"]))
        print("{: <30} {: <80}".format(*[m + " help", "Same as %s (prints this help screen)" % m]))
        print("{: <30} {: <80}".format(*[m + " functions <module>", "Prints all functions. If opt. <module> is provided only prints functions in that loaded module"]))
        print("{: <30} {: <80}".format(*[m + " datasets <integration> <instance>", "Prints all datasets. If opt. <integration> is provided, only prints data sets in that integration. Opt. <instance> can also be provided to further limit returned datasets"]))
        print("{: <30} {: <80}".format(*[m + " debug", "Sets an internal debug variable to True (False by default) to see more verbose info about connections"]))
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

  # This is the magic name.
    @line_cell_magic
    def doc(self, line, cell=None):
        ccell = None
        cline = line.strip().lower()
        if cell is not None:
            ccell = cell.strip().lower()
        if ccell is None: # Line only magic submitted
            if (cline == "") or cline.find("help") == 0:
                self.customHelp()
            elif cline.find("debug") == 0:
                self.debug = not self.debug
            elif cline.find("functions") == 0:
                self.listFunctions(cline)
            elif cline.find("datasets") == 0:
                self.listDatasets(cline)
        else: # This is a cell (or a cell + line) call 
            if cline == "":
                searchtype = "all"
                self.searchFunctions("functions", ccell)
                self.searchDatasets("datasets", ccell)
            elif cline.find("datasets") == 0:
                self.searchDatasets(cline, ccell)
            elif cline.find("functions") == 0:
                self.searchFunctions(cline, ccell)

    def searchFunctions(self, myline, mycell):
        mymod = myline.replace("functions", "").strip()
        modsearch = "all"
        if mymod == "":
            modsearch = "all"
        else:
            if mymod not in self.documented_mods:
                print("Module %s is not in documented mods. Setting scope to all" % mymod)
                modsearch = "all"
            else:
                modesearch = mymod
        print("Function searching not fulling implemeted")
        print("Function Search Scope: %s" % modsearch)
        print("Function Search Term: %s" % mycell)
        print("")

    def listFunctions(self, myline):
        mymod = myline.replace("functions", "").strip()
        if mymod != "" and mymod not in self.documented_mods:
            print("Required module for listing %s does not exist in documented module list: %s" % (mymod, self.documented_mods))
        else:
            for m in self.documented_funcs:
                if mymod == "" or m == mymod:
                    for f in self.documented_funcs[m].keys():
                        func = self.documented_funcs[m][f]
                        print("-------------------------------------------------")
                        print("Function: %s" % f)
                        print("Call: %s" % func['call_name'])
                        print("Location: %s" % func['func_location'])
                        print("")
                        print("Docs:")
                        print(func['docs'])
                        print("")
   
    def searchDatasets(self, myline, mycell):
        print("Dataset Documentation not yet implemented")
        print("")

    def listDatasets(self, myline):
        print("Dataset Documentation not yet implemented")
        print("")




    def parse_doc(docstr):
        ret = OrderedDict({"funcname": "", "shortdesc": "", "desc": "", "writtenby": "", "keywords": [], "callexample": "", "arguments":[], "returns": []})

        myiter = iter(docstr.split("\n"))
        for l in myiter:
            myline = l.strip()
            if ret["funcname"] == "":
                t = myline.split(" - ")
                ret["funcname"] = t[0]
                ret["shortdesc"] = t[1]
            elif ret["desc"] == "":
                if myline.find("Description") == 0:
                    tdesc = ""
                    nl = next(myiter)
                    mynline = nl.strip()
                    while mynline != "":
                        tdesc += mynline + "\n"
                        nl = next(myiter)
                        mynline = nl.strip()
                    ret["desc"] = tdesc[0:-1]
            elif ret["writtenby"] == "":
                if myline.find("Written by:") == 0:
                    twrittenby = ""
                    nl = next(myiter)
                    mynline = nl.strip()
                    while mynline != "":
                        twrittenby += mynline + "\n"
                        nl = next(myiter)
                        mynline = nl.strip()
                    ret["writtenby"] = twrittenby[0:-1]
            elif ret["keywords"] == []:
                if myline.find("Keywords") == 0:
                    tkeywords = []
                    nl = next(myiter)
                    mynline = nl.strip()
                    while mynline != "":
                        tkeywords += mynline.split(",")
                        nl = next(myiter)
                        mynline = nl.strip()
                    ret["keywords"] = tkeywords
            elif ret["callexample"] == "":
                if myline.find("Call Example") == 0:
                    tcallexample = ""
                    nl = next(myiter)
                    mynline = nl.strip()
                    while mynline != "":
                        tcallexample += mynline + "\n"
                        nl = next(myiter)
                        mynline = nl.strip()
                    ret["callexample"] = tcallexample[0:-1]
            elif ret["arguments"] == []:
                if myline.find("Arguments") == 0:
                    targuments = []
                    nl = next(myiter)
                    mynline = nl.strip()
                    while mynline != "" and mynline != "None":
                        targ = mynline.split(" - ")
                        targuments.append(targ)
                        nl = next(myiter)
                        mynline = nl.strip()
                    ret["arguments"] = targuments
            elif ret["returns"] == []:
                if myline.find("Returns") == 0:
                    treturns = []
                    nl = next(myiter)
                    mynline = nl.strip()
                    while mynline != "" and mynline != "None":
                        tret = mynline.split(" - ")
                        treturns.append(tret)
                        nl = next(myiter)
                        mynline = nl.strip()
                    ret["returns"] = treturns
        return ret

    def dedupe_funcs(self, funcs, modname):
        dfuncs = {}       
        for f in funcs:
            if f != [] and f is not None:
                try:
                    n = f['name']
                except:
                    print(f)
                if n != "doc_funcs":
                    fn = f['full_name']
                    d = f['docs']
                    dd = self.parse_doc(d)
                    if n in dfuncs:
                        if dfuncs[n]['docs'] != d:
                            print("same name different docs")
                        if modname == fn.replace("." + n, ""):
                            dfuncs[n]['call_name'] = fn
                        else:
                            dfuncs[n]['func_location'] = fn.replace("." + n, "")
                    else:
                        dfuncs[n] = {"name": n, "docs": d, "docs_dict": dd, "call_name": "", "func_location": ""}
                        if modname == fn.replace("." + n, ""):
                            dfuncs[n]['call_name'] = fn
                        else:
                            dfuncs[n]['func_location'] = fn.replace("." + n, "")
        return dfuncs


    def recursemod(self, modname, startmod=None):
        funcs = []
        bstart = False
        # How to import smod
        if startmod is None:
            startmod = modname
            bstart = True
        
        bmod = modname.split(".")[0]
        if bmod != modname:
            exmod = modname.replace(bmod + ".", "")
            emod = 'sys.modules["' + bmod + '"].' + exmod
        else:
            exmod = ""
            emod = 'sys.modules["' + bmod + '"]'
        if self.debug:
            print("---New Module---------------------------")
            print("modname: %s" % modname)
            print("bmod: %s" % bmod)
            print("emod: %s" % emod)
            print("exmod: %s" % exmod)
            print("startmod: %s" % startmod)
            print("")
        for i in dir(eval(emod)):
            #basemod = modname.split(".")[0]
            if i.find("__") < 0 and i != modname and i != bmod and i != startmod:
                if exmod == "":
                    curmod = bmod + "." + i
                    evalmod = 'sys.modules["' + bmod + '"].' + i
                else:
                    curmod = bmod + "." + exmod + "." + i
                    evalmod = 'sys.modules["' + bmod + '"].' + exmod + "." + i
 
                curtype = str(type(eval(evalmod)))
                curdict = {}
                if curtype.find("'function'") >= 0:
                    if self.debug:
                        print("--Func-----")
                        print("curmod: %s" % curmod)
                        print("evalmod: %s" % evalmod)
                        print("curtype: %s" % curtype)

                    tdocs = eval(evalmod + ".__doc__")
                    if tdocs is None:
                        curdoc = ""
                    else:
                        curdoc = tdocs.strip()
                    curdict = OrderedDict({"name": i, "full_name": curmod, "docs": curdoc})
                    funcs.append(curdict)
                elif curtype.find("'module'"):
                    if self.debug:
                        print("--Mod-----")
                        print("curmod: %s" % curmod)
                        print("evalmod: %s" % evalmod)
                        print("curtype: %s" % curtype)
                    try:
                        newmod = eval(evalmod + ".__package__")
                        if self.debug:
                            print("newmod: %s " % newmod)
                            print("startmod: %s" % startmod)
    
                        if newmod.find(startmod) >= 0:
                            tfuncs = self.recursemod(curmod, startmod)
                            funcs += tfuncs
                    except:
                        print("Error eval(%s.__package)" % evalmod)
                else:
                    print("Other: %s - Type: %s" % (curmod, curtype))
        return funcs

