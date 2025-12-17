#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import textwrap
import sys
import os
import time
from collections import OrderedDict
import requests
import pickle
import hashlib
from pathlib import Path
import ast

from copy import deepcopy
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Markdown, Javascript, FileLink, FileLinks, Image
import pandas as pd
# Widgets
from ipywidgets import GridspecLayout, widgets
import jupyter_integrations_utility as jiu

from jupyter_integrations_utility.funcdoc import print_query, get_func_doc_item, main_help



import importlib
from sharedfx_core._version import __desc__



from addon_core import Addon

@magics_class
class Sharedfx(Addon):
    # Static Variables
    magic_name = "sharedfx"
    name_str = "sharedfx"

    custom_evars = ["sharedfx_shared_dir"]
    custom_allowed_set_opts = ["sharedfx_shared_dir"]

    myopts = {}
    myopts['sharedfx_addon_dir'] = ['~/.ipython/integrations/' + name_str, "Directory for sharedfx caching/configs"]
    myopts['sharedfx_cache_filename'] = ["sharedfx.cache", "Filename for sharedmod caching"]
    myopts['sharedfx_shared_dir'] = ["", "Directory for shared functions. Typically a network share"]
#    evars = []

##
#    loaded_hash = {}
#    all_fx = {}
#    all_funcs = []
##

    sharedfx_dir = None
    sharedfx_hash_file = None
    sharedfx_hash = None

    cache_dir = None
    cache_hash_file = None
    cache_file = None
    cache_hash = None

    sharedfx_doc_index = {}

    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Sharedfx, self).__init__(shell, debug=debug)
        self.debug = debug

        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]

        if "loaded_fx" not in self.ipy.user_ns:
            self.ipy.user_ns["loaded_fx"] = {}


        self.load_env(self.custom_evars) # Called in addon core - Should make it so mods are generic. 

        self.setAddonPath()
        self.setSharedPath()

        self.load_fx_docs()


    def setAddonPath(self):
        tstorloc = self.opts['sharedfx_addon_dir'][0]
        if tstorloc[0] == "~":
            myhome = jiu.getHome(debug=self.debug)
            thome = tstorloc.replace("~", myhome)
            if self.debug:
                print(thome)
            tpdir = Path(thome)
        else:
            tpdir = Path(tstorloc)
        if self.debug:
            print(tpdir)
        self.cache_dir = tpdir
        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.cache_hash_file = self.cache_dir / "func_hash.txt"
        self.cache_file = self.cache_dir / "func_cache.pkl"

    def setSharedPath(self):
        shared_path = None
        shared_dir = self.opts['sharedfx_shared_dir'][0]
        if shared_dir != '':
            shared_path = Path(shared_dir)
            if not os.path.isdir(shared_path):
                print("****** WARNING")
                print(f"Shared Function Directory Path: {shared_path} is not a valid directory  - SHARED OPERATIONS DISABLED")
                shared_path = None
            else:
                shared_dir = Path(shared_dir)
        else:
            print("Shared Location not set - Please set via persist_shared_dir or via ENV variable JUPYTER_PERSIST_SHARED_DIR")
            shared_path = None

        self.sharedfx_dir = shared_path
        if shared_path is not None:
            self.sharedfx_hash_file = self.sharedfx_dir / "func_hash.txt"


    def load_fx_docs(self):
        # Load the docs (whether from cache or direct)

        full_reload = False

        if self.cache_hash_file is not None and os.path.isfile(self.cache_hash_file):
            try:
                self.cache_hash = self.cache_hash_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading cached shared fx hash file at {self.cache_hash_file} - {e}")
                self.cache_hash = None
        else:
            self.cache_hash = None

        if self.sharedfx_hash_file is not None and os.path.isfile(self.sharedfx_hash_file):
            try:
                self.sharedfx_hash = self.sharedfx_hash_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading shared fx hash file at {self.sharedfx_hash_file} - {e}") 
                self.sharedfx_hash = None
        else:
            # Since this doesn't exist, we are going to create it
            if self.sharedfx_hash_file is not None:
                self.sharedfx_hash = self.hashSharedLocation()
                self.saveHashFile(self.sharedfx_hash, self.sharedfx_hash_file)

        if self.sharedfx_hash is None:
            print(f"Could not load Shared FX Location at {self.sharedfx_dir}")
            print(f"Shared Functions Not Loaded")
            return None

        if  self.cache_hash is None:
            full_reload = True # No Cache, need to read everything
        else:
            if self.sharedfx_hash != self.cache_hash:
                full_reload = True # Hashes don't match, need to reload index
            else:
                if self.debug:
                    print("Loading Cache")
                bCache = self.loadCacheFile() # Load from Cache!

                if not bCache:      # We asked to load from cache, but it didn't work. Doing full Reload
                    full_reload = True
                    print(f"Cache Load requested and Failed - Loading Index from SharedFX dir (Slow!)")
                else:
                    if self.debug:
                        print(f"Cache loaded with {len(self.sharedfx_doc_index)} items")

        if full_reload:
            # Reload all Docs # Either the cache didn't exist, it didn't match, or there was an error loading it
            print(f"Full FX Doc Reload required due to lack of local cache or outdated local cache. This is slow, but should be rare!")
            self.reloadFX()
            # Save Cache
            self.saveCacheFile()
            # Save Cached Hash
            self.saveHashFile(self.sharedfx_hash, self.cache_hash_file)

## End Init Functions



    def calculaterGroups(self):

        for k, v in self.sharedfx_doc_index.items():
            file_group = v.get("file_grp", "")


#### Integrations required items
    def retCustomDesc(self):
        return __desc__


    def customHelp(self, curout):
        n = self.magic_name
        m = "%" + n
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout

        out += f"## {n} usage\n"
        out += "---------------\n"
        out += "\n"
        out += f"### {m} line magic\n"
        out += "---------------\n"
        out += "Interacting with specfics parts of the shared function system\n\n"
        out += table_header
        out += f"| {m} clearcache <noreload> | Clears local fx doc cache. If you specify noreload it won't auto reload (dangerous) |\n"
        out += f"| {m} reloadfx | Reload the Functions Dir (Nice if Shared FX are updated and you don't want to reload kernel)|\n"
        out += f"| {m} display `fxname` | Show documentation on a specific function `fxname` |\n"
        out += f"| {m} fq `fxname` | Same as display, but shorter (Thank you Bryant) Show documentation on a specific function `fxname` |\n"



#        out += f"| {m} list modname | Show all documented functions in the 'modname' module |\n"
#        out += f"| {m} list `fxname` | Show the documentation for the 'fxname' function as formatted in list |\n"
        out += "\n\n"
       # out += "### %s cell magic\n" % (mq)
       # out += "-------------------\n"
       # out += "Running searches and obtaining results back from the shared function system\n\n"
       # out += table_header
       # out += "| %s | 'scope' is the search scope (name, kw, desc, author) (can provide multiple, leave blank for all) and the 'query' are the keywords searched |\n" % (mq + " scope<br>query")
       # out += "| %s | Search for any functions related to geoip |\n" % (mq + "<br>geoip")
       # out += "| %s | Search for any function where the description has  active directory |\n" % (mq + " desc<br>active directory")
       # out += "\n"

        return out
#### 

    def reloadFX(self):
        doc_index, doc_dups = self.load_all_shared_includes()
        ignore_list = ['get_doc']

        doc_dups_final = {}
        if not self.debug:
            for k, v in doc_dups.items():
                if k not in ignore_list:
                    doc_dups_final[k] = v
        else:
            doc_dups_final = doc_dups


        if len(doc_dups_final) > 0:
            print(f"Shared Functions Loaded However the following functions are defined in several places (only first is loaded):")
            for k, v in doc_dups_final.items():
                print(f"Loaded: {k} - {doc_index[k]['file_src']}")
                for i in v:
                    print(f"   Dup: {k} - {i['file_src']} (Not Loaded)")
        self.sharedfx_doc_index = doc_index


# Loading Shared Includes 


    def load_all_shared_includes(self):
        doc_index = {}
        doc_dups = {}
        my_path = self.sharedfx_dir
        for py in my_path.glob("*.py"):
            this_index = self.scan_include_file(py)
            for k, v in this_index.items():
                if k not in doc_index:
                    doc_index[k] = v
                else:
                    if k in doc_dups:
                        doc_dups[k].append(v)
                    else:
                        doc_dups[k] = [v]
        return doc_index, doc_dups


    def scan_include_file(self, shared_file_path):
        # This load an include file and parses all it's functions
        out_dict = {}
        src = shared_file_path.read_text(encoding='utf-8')
        tree = ast.parse(src, filename=str(shared_file_path))

        file_group = str(shared_file_path).split("\\")[-1].replace("_helper.py", "").replace(".py", "")
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node, clean=False)
                if not doc:
                    out_dict[node.name] = {"name": node.name, "file_group": file_group, "group": "Unparse", "file_src": str(shared_file_path), "desc": "No doc strings"}
                    if self.debug:
                        print(f"No docs: {node.name}")
                        continue
                try:
                    if doc.strip().find('{"name":') == 0:
                        meta = json.loads(doc)
                        func_name = meta.get("name", None)
                        func_group = meta.get("group", None)
                        if func_group is None:
                            meta['group'] = "No Group"
                        meta['file_src'] = str(shared_file_path)
                        meta['file_group'] = file_group
                        if func_name not in out_dict:
                            out_dict[func_name] = meta
                        else:
                            print(f"Duplicate name {func_name} in node {node.name} in file {shared_file_path}")
                    else:
                        if self.debug:
                            print("No 'name' found at the beginning of doc strings in {node.name}")
                            out_dict[node.name] = {"name": node.name, "group": "Unparse", "file_group": file_group, "file_src": str(shared_file_path), "desc": "Non-compatible Docstrings"}
                except Exception as e:
                    if self.debug:
                        print(f"Error parsing docstring for {node.name}: {str(e)}")
                    out_dict[node.name] = {"name": node.name, "group": "Unparse", "file_group": file_group, "file_src": str(shared_file_path), "desc": f"Exception Parsing: {str(e)}"}
        return out_dict


## Cache/Hash File Helpers


    def loadCacheFile(self):
        bCacheLoad = False
        try:
            if os.path.isfile(self.cache_file):
                with open(self.cache_file, 'rb') as r:
                    self.sharedfx_doc_index = pickle.load(r)
                bCacheLoad = True
        except Exception as e:
            print(f"Load of Cache File PKL requested and failed due to {e}")
            self.sharedfx_doc_index = None
        return bCacheLoad

    def saveCacheFile(self):
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.sharedfx_doc_index, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Error Saving Index to Cache File - {e}")

    def saveHashFile(self, str_hash, hash_loc):
        try:
            with open(hash_loc, "w") as wf:
                wf.write(str_hash)
        except Exception as e:
            print(f"Error saving hash {str_hash} to hash_location: {hash_loc}")


    def hashFile(self, file_path):
        chunk = 1024 * 1024
        h = hashlib.sha256()
        n = 0
        with file_path.open("rb") as f:
            while True:
                b = f.read(chunk)
                if not b: break
                h.update(b)
                n += len(b)
        return h.hexdigest(), n

    def hashSharedLocation(self):
        my_path = self.sharedfx_dir
        my_files = sorted(list(my_path.glob("*.py*")))
        hash_string = ""
        for f in my_files:
            myhash, mysize = self.hash_file(f)
            hash_string += myhash
        ho = hashlib.sha256(hash_string.encode('utf-8'))
        final_hash = ho.hexdigest()
        return final_hash






##### Formatting Functions


    def isQueryFunc(self, func_name):
        bQueryFunc = False
        doc_dict = self.sharedfx_doc_index.get(func_name, None)

        if doc_dict is not None:
            for a in doc_dict.get('args', []):
                if a.get('name', "") == 'print_only':
                    bQueryFunc = True
                    break
        return bQueryFunc


    def formatFXDocs(self, func_name):
        out_md = ""

        bQueryFunc = False

    # Get Doc Dict
        doc_dict = self.sharedfx_doc_index.get(func_name, None)


    # Check for it being a query function

        if doc_dict is not None:

            bQueryFunc = self.isQueryFunc(func_name)
            out_md += f"# {doc_dict['name']}\n\n"
            out_md += f"From {doc_dict['file_group']}\n"
            out_md += f"{doc_dict['file_src']}\n\n"
            out_md += "---------------\n"

            if doc_dict['integration'] != 'na' and doc_dict['instance'] != 'na':
                out_md += f"**Integration:** {doc_dict['integration']} - **Instance(s):** {doc_dict['instance']}\n\n"
                out_md += "--------------------\n"

            out_md += f"**Description:** {doc_dict['desc']}\n\n"
            out_md += f"**Returns:** {doc_dict['return']}\n\n"

            if doc_dict['access_instructions'] != "na":
                out_md += "------------------\n"
                out_md += f"**Access Instructions:** {doc_dict['access_instructions']}\n\n"

            if bQueryFunc == True:
                out_md += f"In addition to print_only, you can print the underlying query by typing: `{doc_dict['name']}([])` or `{doc_dict['name']}()`\n\n"

            out_md += "------------------------\n"
            if len(doc_dict['examples']) > 0:
                out_md += "**Examples**\n\n"
                out_md += "---------------------\n"
                out_md += "| Example | Notes |\n"
                out_md += "| ------- | ----- |\n"
                for e in doc_dict['examples']:
                    ex = ""
                    nt = ""
                    if isinstance(e, list):
                        ex = e[0]
                        nt = e[1]
                    else:
                        if e.find("#") >= 0:
                            ex = e.split("#")[0]
                            nt = e.split("#")[1]
                        else:
                            ex = e
                            nt = "N/A"
                    out_md += f"| `{ex}` | {nt} |\n"
                out_md += "\n"


            out_md += "## Arguments\n"
            out_md += "---------------------\n"
            out_md += "| Arg | Req? | Default | Type | Description|\n"
            out_md += "| --- | ---- | ------- | ---- | -----------|\n"
            for a in doc_dict['args']:
                out_md += f"| {a['name']} | {a['required']} | {a['default']} | {a['type']} | {a['desc']} |\n"
            out_md  += "\n"

            if len(doc_dict['limitations']) > 0:
                out_md += "### Limitations and Notes\n"
                out_md += "------------\n"
                for l in doc_dict['limitations']:
                    out_md += f"- {l}\n"
        else:
            out_md = f"Function {func_name} not found in doc index"
        return out_md

############## Line Magic Functions

    def clearCache(self, reload_line):
        reload = True
        if reload_line.find("noreload") >= 0:
            reload=False

        print(f"Clearing Cache")
        print(f"Removine Cache File")
        try:
            os.remove(self.cache_file)
            self.cache_file = None
        except Exception as e:
            print(f"Cache File removal error: {e}")
        print(f"Removing Cache Hash File")
        try:
            os.remove(self.cache_hash_file)
            self.cache_hash_file = None
            self.cache_hash = None
        except Exception as e:
            print(f"Cache Hash File Removal error: {e}")
        if reload:
            print(f"Reloading Cache")
            self.setAddonPath()
            self.load_fx_docs()
        else:
            print("No reload - Things could get weird")

    def fq(self, line):
        this_func = line.replace("fq ", "").replace("display ", "").strip()
        func_md = self.formatFXDocs(this_func)
        return func_md

    # This is the magic name.
    @line_cell_magic
    def sharedfx(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations.
                if line.lower().find("clearcache") == 0:
                    self.clearCache(line)
                elif line.lower().find("reloadfx") == 0:
                    self.load_fx_docs()
                elif line.find("display") == 0 or line.find("fq") == 0:
                    jiu.displayMD(self.fq(line))

                else:
                    print("Unknown line magic for sharedfx")
        else: # This is a cell (or a cell + line) call
            jiu.displayMD(self.handleSearch(line, cell))


