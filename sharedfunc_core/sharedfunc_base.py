#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import textwrap
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
# Widgets
from ipywidgets import GridspecLayout, widgets

import importlib

from addon_core import Addon

@magics_class
class Sharedfunc(Addon):
    # Static Variables
    magic_name = "funcs"
    name_str = "sharedfunc"
    mods = {}

    custom_evars = ['sharedfunc_ver_check_delta']

    custom_allowed_set_opts = ['sharedfunc_max_full_results', 'sharedfunc_ver_check_delta']

    myopts = {}
    myopts['sharedfunc_max_full_results'] = [1, "When searching, if your results are above this number it only returns the function name and keywords, otherwise it returns full description"]
    myopts['sharedfunc_ver_check_delta'] = [86400, "Number of seconds between version checks - 86400 is one day."]
    myopts['sharedfunc_addon_dir'] = ['~/.ipython/integrations/' + name_str, "Directory for sharedmod caching/configs"]
    myopts['sharedfunc_cache_filename'] = ["modver.cache", "Filename for sharedmod caching"]
#    evars = []
    gflat = {}


#  JUPYTER_SHAREDFUNC_URL_MM="mymod@https://raw.githubusercontent.com/JohnOmernik/sharedmod/main/mymod/_funcdocs.py"

    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Sharedfunc, self).__init__(shell, debug=debug)
        self.debug = debug

        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]

        self.addon_evars += ["_url_"]

        self.load_env(self.custom_evars) # Called in addon core - Should make it so mods are generic. 
        shell.user_ns['sharedfunc_var'] = self.creation_name

        self.init_mods()
        
    def init_mods(self):
        for m in self.mods:
            mloaded = False
            load_error = ""
            try:
                tmod = importlib.import_module(self.mods[m]['realname'])
                mloaded = True
            except Exception as e:
                str_err = str(e)
                load_error += "Module import failed: %s\n" % str_err
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

    def fill_mods(self, mod_name, url):
        mod_realname = url.split("@")[0]
        mod_giturl = url.split("@")[1]
        self.mods[mod_name] = {"realname": mod_realname , "url": mod_giturl, "url_ver": None, "imported": False, "import_ver": None, "import_msg": "", "funcdict": None}



    def check_mod_ver(mod):
        tstorloc = self.opts['sharedfunc_addon_dir'][0]
        if tstorloc[0] == "~":
            myhome = self.getHome()
            thome = tstorloc.replace("~", myhome)
            if self.debug:
                print(thome)
            tpdir = Path(thome)
        else:
            tpdir = Path(tstorloc)
        if self.debug:
            print(tpdir)

        self.sharedfunc_dir = tpdir
        if not os.path.isdir(self.sharedfunc_dir):
            os.makedirs(self.sharedfunc_dir)

        self.sharedfunc_modcache = self.sharedfunc_dir / self.opts['sharedfunc_cache_filename'][0]

        if os.path.isfile(self.sharedfunc_modcache):
            self.modcache = self.load_cache()
        else:
            self.modcache = {}

#    def seed_cache(self, cache_file):
#        lookup_time = int(time.time())
#        for m in self.mods(keys):
#            cmod = self.mods[m]
#            modname = cmod['realname']
#            url = mod['url']
#            urlver = self.get_mod_url_ver(url)



    # Needs to check certs someday
#    def get_mod_url_ver(self, url):
#        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#        results = requests.get(url, verify=False)
#        retver = "0.0.0"
#        if results.status_code != 200:
#            print("Error getting mod current version")
#            if debug:
#                print("Status Code: %s" % results.status_code)
#                print("Error: %s" % results.text)
#            retver = "0.0.0"
#        else:
#            try:
#                j = results.json()
#                retver = j['modvers']
#            except:
#                print("Error getting json")
#                retver = "0.0.0"
#        return retver

    def load_cache(self):
        r = open(self.sharedfunc_modcache, "r")
        rall = r.readall()
        r.close()
        mlist = rall.split("\n")
 #       mymod,2335424243,version
        retmods = {}
        for m in mlist:
            mdata = m.split(",")
            retmods[m[0]] = {"lastcheck": m[1], "version": m[2]}
        return retmods


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
        for f in ff.keys():
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


    def handleSearch(self, l, c):
        if self.debug:
            print("Line: %s" % l)
            print("Cell: %s" % c)
        myScore = self.searchFuncs(c, l)
        if self.debug:
            print("Raw myScore: %s" % myScore)
        sortedScore = dict(sorted(myScore.items(), key=lambda item: item[1][1], reverse=True))
        out = ""
        out += "## Function Search Results\n"
        out += "------------\n"
        out += "### Search Term: %s\n" % c.strip()
        out += "----------------\n"
        for x in sortedScore.keys():
            out += "<details>\n<summary>%s - Score: %s</summary>\n\n" % (x, sortedScore[x][1]) 
            out += self.retSingleFunc(x)
            out += "</details>\n\n"

#        out += "| Search Score | Module | Name | Full Name | Desc | Keywords |\n"
#        out += "| ------------ | ------ | ---- | --------- | ---- | -------- |\n"
#        for x in sortedScore.keys():
#            out += "| %s | %s | %s | %s | %s | %s |\n" % (sortedScore[x][1], x.split(",")[0], self.gflat[x]['name'], x, "<br>".join(textwrap.wrap(self.gflat[x]['description'], 40)), self.gflat[x]['keywords'])
        out += "\n\n"
        return out


 #       pFull = True
 #       if len(sortedScore.keys()) > self.opts['sharedfunc_max_full_results'][0]:
 #           pFull = False
 #       for x in sortedScore.keys():
 #           print("%s - Score: %s" % (x, sortedScore[x][1]))
 #           if pFull:
 #               self.displayFunc(x)

    def flatfuncs(self, troot, basename):
        tret = {}
        for f in troot['funcs']:
            n = f['name']
            tn = basename + "." + n
            tret[tn] = {**f}
            tret[tn]['fullname'] = tn
        for c in troot['children'].keys():
            tb = basename + "." + c
            tret.update(self.flatfuncs(troot['children'][c], tb))
        return tret


    def retSingleFunc(self, fname):
        f = self.gflat[fname]
        modalias = fname.split(".")[0]
        modname = self.mods[modalias]['realname']

        out = ""
        out += "## %s\n" % fname
        out += "-----------------\n"
        out += "`import %s as %s`\n\n" % (modname, modalias)
        out += "| Author | Keywords |\n"
        out += "| --- | ---- |\n"
        out += "| %s | %s |\n" % (f['authors'], f['keywords'])
        out += "\n\n"
        out += "%s\n\n" % f['description']
        out += "#### Arguments\n---------\n"
        out += "| Name | Type | Req/Opt | Desc |\n"
        out += "| ---- | ---- | ------- | ---- |\n"
        for a in f['args']:
            out += "| %s | %s | %s | %s |\n" % (a[0], a[1], a[2], "<br>".join(textwrap.wrap(a[3],  40)))
        out += "\n\n"
        out += "#### Returns\n----------\n"
        out += "| Type | Desc |\n"
        out += "| ---- | ---- |\n"
        for r in f['returns']:
            out += "| %s | %s |\n" % (r[0], r[1])
        out += "\n\n"
        out += "#### Usage:\n---------\n"
        out += "```\n%s\n```\n" % (f['usage'])
        out += "\n\n"

        return out


    def displayFuncs(self, fname):
        #self.displayFunc(line.replace("display", "").strip())

        out = ""
        out += "# Function Display\n"
        out += "----------\n"

        found = []
        if fname in self.gflat.keys():
            found.append(fname)
        else:
            for n in self.gflat.keys():
                if fname == self.gflat[n]['name']:
                    found.append(n)
        out += "%s Functions Returned that match search term: %s\n\n" % (len(found), fname)
        for f in found:
            out += self.retSingleFunc(f)

        if out [-2:0] != "\n\n":
            out += "\n\n"

        return out


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


    def retFuncs(self, mod):
        if mod == "":
            tmod = None
        else:
            tmod = mod
        out = ""
        out += "# Function Listing\n"
        out += "--------------\n"
        out += "Module Filter: %s\n\n" % tmod
        out += "| Module | Name | Full Name | Desc | Keywords |\n"
        out += "| ------ | ---- | --------- | ---- | -------- |\n"
        for m in self.gflat.keys():
            if tmod is None or m.find(tmod) == 0:
                out += "| %s | %s | %s | %s | %s |\n" % (m.split(".")[0], self.gflat[m]['name'], self.gflat[m]['fullname'], "<br>".join(textwrap.wrap(self.gflat[m]['description'], 40)), self.gflat[m]['keywords'])
        out += "\n\n"
        return out

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

    def fixOut(self, instr):
        out = instr.strip().replace("\n", "<br>")
        return out

    def retMods(self):
        out = ""
        out += "# Modules Defined in Environment\n"
        out += "--------------\n"

        table_header =  "| Module | Loaded As | Imported | Import Message | Import Ver | Repo URL | Repo Ver |\n"
        table_header += "| ------ | --------- | -------- | -------------- | ---------- | -------- | -------- |\n"
        out += table_header
        for m in self.mods.keys():
            tmod = self.mods[m]
            out += "| %s | %s | %s | %s | %s | %s | %s |\n" % (m, tmod['realname'], tmod['imported'], self.fixOut(tmod['import_msg']), tmod['import_ver'], tmod['url'], tmod['url_ver'])
        out += "\n\n"
        return out

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

    def customHelp(self, curout):
        n = self.magic_name
        m = "%" + n
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout

        out += "## %s usage\n" % n
        out += "---------------\n"
        out += "\n"
        out += "### %s line magic\n" % (m)
        out += "---------------\n"
        out += "Interacting with specfics parts of the shared function system\n\n"
        out += table_header
        out += "| %s | List the requested modules, and their relavent information including import status |\n" % (m + " mods")
        out += "| %s | Show the actual import lines (in the next cell) for the successfully imported modules |\n" % (m + " imports")
        out += "| %s | Show all documented functions handled by shared funcs |\n" % (m + " list")
        out += "| %s | Show all documented functions in the 'modname' module |\n" % (m + " list 'modname'")
        out += "| %s | Show the documentation for the 'funcname' function as formatted in list |\n" % (m + " display 'funcname'")
        out += "\n\n"
        out += "### %s cell magic\n" % (mq)
        out += "-------------------\n"
        out += "Running searches and obtaining results back from the shared function system\n\n"
        out += table_header
        out += "| %s | 'scope' is the search scope (name, kw, desc, author) (can provide multiple, leave blank for all) and the 'query' are the keywords searched |\n" % (mq + " scope<br>query")
        out += "| %s | Search for any functions related to geoip |\n" % (mq + "<br>geoip")
        out += "| %s | Search for any function where the description has  active directory |\n" % (mq + " desc<br>active directory")
        out += "\n"

        return out

    def retCustomDesc(self):
        out = "The sharedfunc addon allows you to use the magic function %funcs to provide in notebook documentation for shared functions through a common repository"
        return out

    # This is the magic name.
    @line_cell_magic
    def funcs(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations. 
                if line.find("mods") == 0:
                    self.displayMD(self.retMods())
#                    self.listmods()
                elif line.find("list") == 0:
                    self.displayMD(self.retFuncs(line.replace("list", "").strip()))
#                    self.listFuncs(line.replace("list", "").strip())
                elif line.find("imports") == 0:
                    self.showActiveImports(line)
                elif line.find("display") == 0:
#                    self.displayFunc(line.replace("display", "").strip())
                    self.displayMD(self.displayFuncs(line.replace("display", "").strip()))
                else:
                    print("Unknown line magic for funcs")
        else: # This is a cell (or a cell + line) call
            self.displayMD(self.handleSearch(line, cell))


