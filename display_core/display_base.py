#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import uuid
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
import jupyter_integrations_utility as jiu
# Widgets
from ipywidgets import GridspecLayout, widgets

try:
    import qgrid
except:
    pass

from addon_core import Addon

@magics_class
class Display(Addon):
    # Static Variables

    magic_name = "display"
    name_str = "display"
    custom_evars = ['display_pd_display_grid']

    custom_allowed_set_opts = [
                              'display_pd_display_idx', 'display_pd_max_colwidth', 'display_pd_display.max_columns', 'display_pd_display_grid',
                              'display_max_rows',
                              'display_qg_header_autofit', 'display_qg_header_pad', 'display_qg_colmin', 'display_qg_colmax', 'display_qg_text_factor',
                              'display_qg_autofit_cols', 'display_qg_defaultColumnWidth', 'display_qg_minVisibleRows', 'display_qg_maxVisibleRows', 'display_qg_display_idx'
                            ]

    pd_set_vars = ['display_pd_display.max_columns', 'display_pd_max_colwidth']

    myopts = {}
    myopts['display_pd_display_idx'] = [False, "Display the Pandas Index with html output"]
    myopts['display_pd_max_colwidth'] = [50, 'Max column width to display when using pandas html output']
    myopts['display_pd_display.max_columns'] = [None, 'Max Columns']
    myopts['display_pd_display_grid'] = ["html", 'How Pandas datasets should be displayed (html, qgrid)']

    myopts['display_max_rows'] = [10000, 'Number of Max Rows displayed']

    myopts['display_qg_header_autofit'] = [True, 'Do we include the column header (column name) in the autofit calculations?']
    myopts['display_qg_header_pad'] = [2, 'If qg_header_autofit is true, do we pad the column name to help make it more readable if this > 0 than it is the amount we pad']
    myopts['display_qg_colmin'] = [75, 'The minimum size a qgrid column will be']
    myopts['display_qg_colmax'] = [750, 'The maximum size a qgrid column will be']
    myopts['display_qg_text_factor'] = [8, 'The multiple of the str length to set the column to ']
    myopts['display_qg_autofit_cols'] = [True, 'Do we try to auto fit the columns - Beta may take extra time']
    myopts['display_qg_defaultColumnWidth'] = [200, 'The default column width when using qgrid']
    myopts['display_qg_minVisibleRows'] = [8, 'The default min number of rows visible in qgrid - This affects the height of the widget']
    myopts['display_qg_maxVisibleRows'] = [25, 'The default max number of rows visible in qgrid - This affects the height of the widget']
    myopts['display_qg_display_idx'] = [False, "Display the Pandas Index with qgrid output"]


    pd.set_option('display.max_columns', myopts['display_pd_display.max_columns'][0])
    pd.set_option('max_colwidth', myopts['display_pd_max_colwidth'][0])

    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first.
    # This is because they are designed to be self documenting.
    # Each option item is actually a list of two length.
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description.


    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables.


    def __init__(self, shell, debug=False,  display_pd_display_grid="html", *args, **kwargs):
        super(Display, self).__init__(shell, debug=debug)
        self.debug = debug

        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)
        if self.opts['display_pd_display_grid'][0] == 'html':
            self.opts['display_pd_display_grid'][0] = display_pd_display_grid

        #shell.user_ns['display_var'] = self.creation_name



    def customHelp(self, curout):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m
        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"
        out = curout
        out += "---------------------\n"
        out += "### %s Specific Line Magics\n" % m
        out += table_header
        out += "| %s | Display the dataframe 'yourdf' (no quotes) |\n" % (m + " 'yourdf'")
        out += "\n\n"
        return out

    def retCustomDesc(self):
        out = "This addon allows you to display dataframes using a standard interface. It is also the default addon called post query by integrations"
        return out

    def qgridDisplay(self, result_df, mycnt):

        # Determine the height of the qgrid (number of Visible Rows)
        def_max_rows = int(self.opts['display_qg_maxVisibleRows'][0])
        def_min_rows = int(self.opts['display_qg_maxVisibleRows'][0])
        max_rows = def_max_rows
        min_rows = def_min_rows
        if mycnt >= def_max_rows:
            max_rows = def_max_rows
            min_rows = def_min_rows
        elif mycnt + 2 <= def_max_rows:
            max_rows = def_max_rows
            min_rows = mycnt + 2

        mygridopts = {'forceFitColumns': False, 'maxVisibleRows': max_rows, 'minVisibleRows': min_rows, 'defaultColumnWidth': int(self.opts['display_qg_defaultColumnWidth'][0])}
        mycoldefs = {}

        # Determine Index width
        if int(self.opts['display_qg_display_idx'][0]) == 1:
            mydispidx = True
        else:
            mydispidx = False
            mycoldefs['index'] = { 'maxWidth': 0, 'minWidth': 0, 'width': 0 }
        if self.debug:
            print("mydispidx: %s" % mydispidx)

        # Handle Column Autofit
        if self.opts['display_qg_autofit_cols'][0] == True:
            maxColumnLenghts = []
            for col in range(len(result_df.columns)):
                maxColumnLenghts.append(max(result_df.iloc[:,col].astype(str).apply(len)))
            dict_size = dict(zip(result_df.columns.tolist(), maxColumnLenghts))
            text_factor = self.opts['display_qg_text_factor'][0]
            colmin = self.opts['display_qg_colmin'][0]
            colmax = self.opts['display_qg_colmax'][0]
            header_autofit = self.opts['display_qg_header_autofit'][0]
            header_pad = self.opts['display_qg_header_pad'][0]
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


        if self.debug:
            print("mygridopts: %s" % mygridopts)
            print("")
            print("mycoldefs: %s" % mycoldefs)
        # Display the QGrid
        display(qgrid.show_grid(result_df, grid_options=mygridopts, column_definitions=mycoldefs))

    def htmlDisplay(self, result_df, mycnt):

        # Set PD Values for html display
        for tkey in self.pd_set_vars:
            tval = self.opts[tkey][0]
            pd.set_option(tkey.replace('display_pd_', ''), tval)

        display(HTML(result_df.to_html(index=self.opts['display_pd_display_idx'][0])))

# This can now be more easily extended with different display types
    def displayDF(self, result_df, instance=None, qtime=None):

        if instance is None:
            instance = "dataframe"

        display_type = self.opts['display_pd_display_grid'][0]
        max_display_rows = self.opts['display_max_rows'][0]
        if result_df is not None:
            mycnt = len(result_df)
        else:
            mycnt = 0

        if qtime is not None:
            print("%s Records from instance %s in Approx %s seconds" % (mycnt, instance, qtime))
            print("")
        else:
            print("%s Records" % (mycnt))
            print("")

        if self.debug:
            print("Testing max_colwidth: %s" %  pd.get_option('max_colwidth'))

        if mycnt == 0:
            pass
        elif mycnt > max_display_rows:
            print("Number of results (%s) from instance %s greater than display_max_rows(%s)" % (mycnt, instance, max_display_rows))
        else:
            if display_type == "qgrid":
                self.qgridDisplay(result_df, mycnt)
            elif display_type == "html":
                self.htmlDisplay(result_df, mycnt)
            else:
                print("%s display type not supported" % display_type)

    def parse_df(self, line):
        tvar = line.strip()
        mydf = None
        dot_df = False
        sq_df = False
        if tvar in self.ipy.user_ns:
        # if it exists in the user namespace
            mydf = self.ipy.user_ns[tvar]
            if isinstance(mydf, pd.DataFrame):
                pass
            else:
                print("%s exists but is not a Pandas Data frame - Not Displaying" % varname)
                print("Type: %s" % type(mydf))
                mydf = None
        else:
            # First try to split based on . and see if the first thing is a dataframe in the user namespace
            dot_df = False
            try:
                dot_var = tvar.split(".")[0]
                if isinstance(self.ipy.user_ns[dot_var], pd.DataFrame):
                    dot_df = True
                    if self.debug:
                        print("%s passed the dot test" % dot_var)
            except:
                pass
            if not dot_df:
                # If mydf. isn't in the card, let's also check for filtering ( mydf[mydf[ )
                sq_df = False
                try:
                    sq_var = tvar.split("[")[0]
                    if isinstance(self.ipy.user_ns[sq_var], pd.DataFrame):
                        sq_df = True
                        if self.debug:
                            print("%s passed the square bracket test" % sq_var)
                except:
                    pass
            if sq_df or dot_df:
                try:
                    tmpdf = eval(tvar)
                    if isinstance(tmpdf, pd.DataFrame):
                        mydf = tmpdf
                    else:
                        print("We were able to process, but it didn't produce a dataframe")
                        print("What we processed: %s" % tvar)
                        print("What it produced: %s" % type(tmpdf))
                        mydf = None
                except Exception as e:
                    print("Could not evaluate the following code into a Dataframe - Not Displaying")
                    print(tvar)
                    print("Error: %s" % str(e))
                    mydf = None
        return mydf


    def line_display(self, line):
        if line.lower().find("display") == 0:
            line = line.replace("display", "").strip()
        curdf = self.parse_df(line)
        if curdf is not None:
            self.displayDF(curdf)
        else:
            print("Could not identifiable dataframe from provided %display magic submission")
            print("Provided value must be a dataframe that exists in the namespace, or evalute to a dataframe")
            print("Please see %display for help")


    # This is the magic name.
    @line_cell_magic
    def display(self, line, cell=None):
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if self.debug:
                print("line: %s" % line)
                print("cell: %s" % cell)
            if not line_handled: # We based on this we can do custom things for integrations. 
                self.line_display(line)
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell data activities")
