# Utility Functions
# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import re
import os
import time
import pandas as pd
import requests
from collections import OrderedDict

from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML

from IPython.display import display_html, display, Markdown, Javascript, FileLink, FileLinks, Image
import ipywidgets as widgets

import jupyter_integrations_utility as jiu


def load_json_config(file_loc="integrations_cfg.py"):

    if not os.path.isfile(file_loc):
        print(f"File {file_loc} does not exist or is not a file. JSON not loaded")
        return None
    f = open(file_loc, "r")
    raw_cfg = f.read()
    f.close()
    cleaned_cfg = ""
    for line in raw_cfg.split("\n"):
        if line.strip().find("#") == 0 or line.strip() == "":
           pass
        else:
            cleaned_cfg += line + "\n"
    try:
        json_cfg = json.loads(cleaned_cfg)

    except Exception as e:
        except_out = str(e)
        print(f"Unable to parse JSON in {file_loc}")
        print(f"Exception: {except_out}")

        if except_out.find(' line '):
            linestart = except_out.find( ' line ')
            colstart = except_out.find(' column ')
            line_num = except_out[linestart:colstart].replace(' line ', '')
            int_line_num = int(line_num)
            ar_cleaned_cfg = cleaned_cfg.split("\n")
            if int_line_num > 1:
                startline = int_line_num - 2
            else:
                startline = 0

            if int_line_num + 1 >= len(ar_cleaned_cfg) - 1:
                endline = None
            else:
                endline = int_line_num + 1
            lines_out = "\n".join(ar_cleaned_cfg[startline:endline])

            print(f"Possible lines of issue are:\n{lines_out}")

        sys.exit(1)

        json_cfg = None

    return json_cfg



def displayMD(md):
    display(Markdown(md))

def getHome(debug=False):
    home = ""
    if "USERPROFILE" in os.environ:
        if debug:
            print("USERPROFILE Found")
        home = os.environ["USERPROFILE"]
    elif "HOME" in os.environ:
        if debug:
            print("HOME Found")
        home = os.environ["HOME"]
    else:
        print("Home not found - Defaulting to ''")
    if home[-1] == "/" or home[-1] == "\\":
        home = home[0:-1]
    if debug:
        print("Home: %s" % home)
    return home


def escapeMD(text):
    firstparse = text.replace("\r\n", "").replace("\n", "")
    parse = re.sub(r"([_*\[\]()~`>\#\+\-=|\.!])", r"\\\1", firstparse)
    reparse = re.sub(r"\\\\([_*\[\]()~`>\#\+\-=|\.!])", r"\1", parse)
    return reparse
