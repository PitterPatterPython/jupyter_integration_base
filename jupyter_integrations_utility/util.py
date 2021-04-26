# Utility Functions
# Base imports for all integrations, only remove these at your own risk!
import json
import sys
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
