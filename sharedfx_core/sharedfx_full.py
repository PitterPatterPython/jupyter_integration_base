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

    sharedfx_docs_index = {}

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


    def load_fx_docs(self):
        # Load the docs (whether from cache or direct)

        full_reload = False

        if self.cache_hash_file is not None and os.path.isfile(self.cache_hash_file):
            try:
                self.cache_hash = cache_hash_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading cached shared fx hash file at {self.cache_hash_file} - {e}")
                self.cache_hash = None
        else:
            self.cache_hash = None

        if self.sharedfx_hash_file is not None and os.path.isfile(self.sharedfx_hash_file):
            try:
                self.sharedfx_hash = shared_hash_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading shared fx hash file at {self.shared_hash_file} - {e}") 
                self.sharedfx_hash = None
        else:
            # Since this doesn't exist, we are going to create it
            self.sharedfx_hash = self.hashSharedLocation()
            self.saveHashFile(self.sharedfx_hash, self.sharedfx_hash_file)

        if self.sharedfx_hash is None:
            print(f"Could not load Shared FX Location at {self.sharedfx_dir}")
            print(f"Shared Functions Not Loaded")
            return None

        if  self.cached_hash is None:
            full_reload = True # No Cache, need to read everything
        else:
            if self.sharedfx_hash != self.cached_hash:
                full_reload = True # Hashes don't match, need to reload index
            else:
                bCache = self.loadCacheFile() # Load from Cache!
                if not bCache:      # We asked to load from cache, but it didn't work. Doing full Reload
                    full_reload = True
                    print(f"Cache Load requested and Failed - Loading Index from SharedFX dir (Slow!)")

        if full_reload:
            # Reload all Docs # Either the cache didn't exist, it didn't match, or there was an error loading it
            print(f"Full FX Doc Reload required due to lack of local cache or outdated local cache. This is slow, but should be rare!")
            doc_index, doc_dups = self.load_all_shared_includes()
            if len(doc_dups) > 0:
                print(f"Shared Functions Loaded However the following functions are defined in several places (only first is loaded):")
                for k, v in doc_dups.items():
                    print("Loaded: {k} - {doc_index[k]['file_src']")
                    for i in v:
                        print("   Dup: {k} - {i['file_src']} (Not Loaded)")
            self.sharedfx_doc_index = doc_index
            # Save Cache
            self.saveCacheFile()
            # Save Cached Hash
            self.saveHashFile(self.shared_fx_hash, self.cache_hash_file)

    def loadCacheFile(self):
        bCacheLoad = False
        try:
            if os.path.isfile(self.cache_file):
                with open(self.session_dict_pkl, 'rb') as r:
                    self.sharedfx_doc_index = pickle.load(r)
                bCacheLoad = True
        except Exception as e:
            print(f"Load of Cache File PKL requested and failed due to {e}")
            self.sharedfx_doc_index = None
        return bCacheLoad

    def saveCacheFile(self):
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.sharedfx_docs_index, f, protocol=pickle.HIGHEST_PROTOCOL)
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
        self.cache_hash_file = self.cache_dir / "func_hash.txt"
        self.cache_file = self.cache_dir / "func_cache.pkl"


    def setSharedPath(self):
        shared_path = None
        shared_dir = self.opts['sharedfx_shared_dir'][0]
        if shared_dir != '':
            shared_path = pathlib.Path(shared_dir)
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

    def scan_include_file(self, shared_file_path):
        # This load an include file and parses all it's functions
        out_dict = {}
        src = shared_file_path.read_text(encoding='utf-8')
        tree = ast.parse(src, filename=str(shared_file_path))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node, clean=False)
                if not doc:
                    out_dict[node.name] = {"name": node.name, "group": "Unparse", "file_src": str(shared_file_path), "desc": "No doc strings"}
                    if self.debug:
                        print(f"No docs: {node.name}")
                        continue
                try:
                    if doc.strip().find('{"name":') == 0:
                        meta = json.loads(doc)
                        func_name = meta.get("name", None)
                        func_group = meta.get("group", None)
                        if func_group is None:
                            meta['group'] = "No Group Defined"
                        meta['file_src'] = str(shared_file_path)
                        if func_name not in out_dict:
                            out_dict[func_name] = meta
                        else:
                            print(f"Duplicate name {func_name} in node {node.name} in file {shared_file_path}")
                    else:
                        if self.debug:
                            print("No 'name' found at the beginning of doc strings in {node.name}")
                            out_dict[node.name] = {"name": node.name, "group": "Unparse", "file_src": str(shared_file_path), "desc": "Non-compatible Docstrings"}
                except Exception as e:
                    if self.debug:
                        print(f"Error parsing docstring for {node.name}: {str(e)}")
                    out_dict[node.name] = {"name": node.name, "group": "Unparse", "file_src": str(shared_file_path), "desc": f"Exception Parsing: {str(e)}"}
        return out_dict



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
        out += "| %{m} mods | List the requested modules, and their relavent information including import status |\n"
        out += "| %{m} imports | Show the actual import lines (in the next cell) for the successfully imported modules |\n"
        out += "| %{m} list | Show all documented functions handled by shared funcs |\n"
        out += "| %{m} list modname | Show all documented functions in the 'modname' module |\n"
        out += "| %{m} list `fxname` | Show the documentation for the 'fxname' function as formatted in list |\n"
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

    def retCustomDesc(self):
        return __desc__


    def refreshFXDicts(self):
        self.loaded_fx = self.ipy.user_ns.get("loaded_fx", {})


    def FXLine(self, line):
        line_split = line.strip().split(" ")
        if len(line_split) == 1:
            this_item = line_split[0]


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
                if line.find("display") == 0:
                    jiu.displayMD(self.displayFuncs(line.replace("display", "").strip()))
                else:
                    print("Unknown line magic for funcs")
        else: # This is a cell (or a cell + line) call
            jiu.displayMD(self.handleSearch(line, cell))


