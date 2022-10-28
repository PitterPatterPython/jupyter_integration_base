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
