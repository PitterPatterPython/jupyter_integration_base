#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
import pandas as pd
from copy import deepcopy


# Plotly
try:
    import plotly.graph_objects as go
    import plotly.express as px
except:
    print("Could not import plotly go or px")

# Requests and BeutifulSoup
try:
    import requests
    from bs4 import BeautifulSoup
except:
    print("Could not import requests or BeutifulSoup")

# Pickle
try:
    import pickle
except:
    print("Could not import pickle")


from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Javascript, FileLink, FileLinks, Image

# Widgets
from ipywidgets import GridspecLayout, widgets


@magics_class
class Visualization(Magics):
    # Static Variables
    ourdf = None            # The df we are working with
    ipy = None              # IPython variable for updating and interacting with the User's notebook
    debug = False           # Enable debug mode
    all_charts = None       # Chart doc data
    show = False            # Should we write output
    base_allowed_set_opts = ['vis_search_prefix'] # These are the variables we allow users to set no matter the inegration (we should allow this to be a customization)

    # Variables Dictionary
    opts = {}


    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first. 
    # This is because they are designed to be self documenting. 
    # Each option item is actually a list of two length. 
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description. 

    opts['vis_search_prefix'] = ["prev_", "The Variable prefix to look for when showing availble dataframes"]
    opts['plotly_doc_cache_enabled'] = [True, "Use a cache file for plotly"]
    opts['plotly_doc_cache_file'] = ["/.ipython/.plotly_doc.pkl", "A cache file to speed up lookups - TEMP"]
    opts['plotly_custom_exclude_list'] = ["", "A list of fields that show up in plotly functions that you may want to exclude in the vis widgets - Comma sep values here, no spaces"] 

    dg = None # The main display grid
    avail_dfs = []
    height = ""
    width = ""
    bDisplayed = False
    # Widget Place holders
    out_graph = None 
    out_url = None
    out_func = None

    btn_add = None
    btn_rem = None
    btn_clear_assigned = None
    btn_gen = None

    lbl_core = None
    lbl_title = None
    txt_title = None

    txt_xaxis = None
    txt_yaxis = None
    lbl_xaxis = None
    lbl_yaxis = None


    txt_names = None
    txt_values = None
    lbl_names = None
    lbl_values = None


    lbl_charth = None
    lbl_chartw = None
    txt_charth = None
    txt_chartw = None


    txt_add1 = None
    txt_add2 = None
    lbl_add1 = None
    lbl_add2 = None

    lbl_break = None

    lbl_cols = None
    lbl_fields = None
    lbl_assigned = None

    sel_cols = None
    sel_fields = None
    sel_assigned = None

    sel_df = None
    drp_charts = None


    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables. 
    def __init__(self, shell, debug=False, width="1500px", height="750px", refresh_plotly_docs=False, plotly_custom_exclude_list="", *args, **kwargs):
        self.debug = debug
        self.width = width
        self.height = height
        super(Visualization, self).__init__(shell)
        self.ipy = get_ipython()
        self.all_charts = self.get_charts(refresh_plotly_docs)
        if plotly_custom_exclude_list != "":
            try:
                arex = plotly_custom_exclude_list.split(",")
                for e in arex:
                    self.opts['plotly_custom_exclude_list'][0].append(e)
            except:
                print("load of exclude list failed")

        try:
            a = type(px)
        except:
            print("Plotly, and plotly express doesn't seem to be installed - This will cause problems for a plotly based vis helper")
        try:
            a = type(requests)
            a = type(BeautifulSoup)
        except:
           print("You need BeautifulSoup and requests as well - make sure these are installed")

        try:
            a = type(pickle)
        except:
            print("Pickle not installed, caching won't work")
    


    @line_magic
    def vis(self, line=None):
        if self.bDisplayed == False:
            self.instantiate_objects()
            self.fill_widgets()
            self.layout_grid()
            self.bDisplayed = True
        
        self.refresh_avail_dfs()

        if self.debug:
            print("Running line magic: value: %s" % line)
        if line.strip() == "" :
            pass
        else:
            self.avail_dfs.append(line.strip())

        self.sel_df.options = self.avail_dfs
        self.show = True
        self.drp_charts.value = "line"
        self.set_vis("line")
        self.df_change(self.sel_df.value)
        self.show = True
        display(self.dg)

    def layout_grid(self):
        if self.debug:
            print("Setting Layout")
        # Organize Layout
        self.dg = GridspecLayout(13, 6, width=self.width, height=self.height)
        # Row 0 - Header
        self.dg[0, 2:4] = self.lbl_core
        #Row 1 - Chart Type and Title
        self.dg[1, 1] = self.drp_charts
        self.dg[1, 3] = self.lbl_title
        self.dg[1, 4] = self.txt_title
        # Row 2 and 3 - Data Frame Selection and chart height/width
        self.dg[2:4, 1] = self.sel_df
        self.dg[2, 3] = self.lbl_charth
        self.dg[2, 4] = self.txt_charth
        self.dg[3, 3] = self.lbl_chartw
        self.dg[3, 4] = self.txt_chartw

        # Rows, 4, 5, and 6 - Field chooser and buttons
        self.dg[4, 1] = self.lbl_fields
        self.dg[4, 2] = self.lbl_cols
        self.dg[4, 4] = self.lbl_assigned
        self.dg[5:7, 1] = self.sel_fields
        self.dg[5:7, 2] = self.sel_cols
        self.dg[5:7, 4] = self.sel_assigned

        self.dg[5, 3] = self.btn_add
        self.dg[6, 3] = self.btn_rem
        # Row Generate code/clear buttons
        self.dg[7, 4] = self.btn_clear_assigned
        self.dg[7, 2:3] = self.btn_gen

        # Row 8 - Display for Full Chart and URL
        self.dg[8, 1:] = self.out_url
        # Row 8 - Display for formatted function
        self.dg[9:11, 1:] = self.out_func
        # Row 9   A Break (This is stupid)
        self.dg[11, :] = self.lbl_break
        # Row 10 - The actual output
        self.dg[12, :] = self.out_graph


    def fill_widgets(self):
        if self.debug:
            print("Filling Widgets")
        # Fill Widgets
        self.drp_charts.options = list(self.all_charts.keys())
        self.refresh_avail_dfs()
        self.sel_df.options = self.avail_dfs
        if self.debug:
            print ("Setting listeners")
        # Set on change listeners
        self.sel_df.observe(self.df_change)
        self.drp_charts.observe(self.update_chart_ops)
        self.btn_gen.on_click(self.gen_vis)
        self.btn_add.on_click(self.add_mapping)
        self.btn_rem.on_click(self.rem_mapping)
        self.btn_clear_assigned.on_click(self.clear_assigned)

    def clear_assigned(self, b):
        self.sel_assigned.options = []
    def add_mapping(self, b):
        mycol = ""
        myfield = ""
        mycol = self.sel_cols.value
        myfield = self.sel_fields.value
        if mycol != "" and myfield != "":
            myassigned = myfield + '="' + mycol + '"'
            curopts = deepcopy(list(self.sel_assigned.options))
            bfound = False
            for c in curopts:
                if c.find(myfield) == 0 or c.find('"'+mycol+'"') >= 0:
                    bfound = True
                    break
            if bfound == False:
                curopts.append(myassigned)
                self.sel_assigned.options = curopts


    def rem_mapping(self, b):
        rem_val = self.sel_assigned.value
        curopts = deepcopy(list(self.sel_assigned.options))
        newopts = []
        for c in curopts:
            if c != rem_val:
                newopts.append(c)
        self.sel_assigned.options = newopts

    def instantiate_objects(self):
        self.out_graph = widgets.Output()
        self.out_url = widgets.Output()
        self.out_func = widgets.Output()

        self.btn_gen = widgets.Button(description="Generate Vis")

        self.btn_add = widgets.Button(description="Add Mapping")
        self.btn_rem = widgets.Button(description="Remove Mapping")
        self.btn_clear_assigned = widgets.Button(description="Clear")

        self.sel_cols = widgets.Select(options=[], disabled=False) 
        self.sel_fields = widgets.Select(options=[], disabled=False)
        self.sel_assigned = widgets.Select(options=[], disabled=False)

        self.lbl_cols = widgets.Label(value="Columns")
        self.lbl_fields = widgets.Label(value="Fields")
        self.lbl_assigned = widgets.Label(value="Assigned")


        self.lbl_core = widgets.Label(value="Visualization Core")
        self.lbl_title = widgets.Label(value="Chart Title:")
        self.txt_title = widgets.Text(value="My Chart")

        self.txt_xaxis = widgets.Text(value = "")
        self.txt_yaxis = widgets.Text(value = "")
        self.lbl_xaxis = widgets.Label(value="X Axis")
        self.lbl_yaxis = widgets.Label(value="Y Axis")

        self.lbl_charth = widgets.Label(value="Chart Height:")
        self.lbl_chartw = widgets.Label(value="Chart Width:")
        self.txt_charth = widgets.Text(value="750")
        self.txt_chartw = widgets.Text(value="2000")
       
        self.lbl_break = widgets.Label(value="---------------------------------------------------------------------------------")

        self.sel_df = widgets.Select(options=[], description='Data Frame:', disabled=False)
        self.drp_charts = widgets.Dropdown(options=[], description='Chart Type:', disabled=False)

    def refresh_avail_dfs(self):
        self.avail_dfs = []
        mykeys = deepcopy(list(self.ipy.user_ns.keys()))
        for x in mykeys:
            if x.find(self.opts['vis_search_prefix'][0]) >= 0:
                self.avail_dfs.append(x)

    def gen_vis(self, b):
        out = ""
        mychart = self.drp_charts.value
        out = "px.%s(" % mychart
    
        out += self.sel_df.value + ', title="%s", ' % self.txt_title.value
        out += "width=%s, height=%s, " % (self.txt_chartw.value, self.txt_charth.value)
        assigned = deepcopy(list(self.sel_assigned.options))
        for a in assigned:
            out+= a + ", "
        out = out[0:-2] + ")"
        if self.show:
            try:
                self.out_graph.clear_output()
                with self.out_graph:
                    print("fig = " + out + "\nfig.show()")
            except:
                print("Out graph error")
    # I wish this worked
    #ipy.set_next_input("fig = " + out + "\nfig.show()") # Doesn't work until the NEXT cell is run. 


    def update_chart_ops(self, change):
        if change['name'] == 'value':
            try:
                new_graph = change['new']
                self.set_vis(new_graph)
            except:
                print("update_chart error")


    def set_vis(self, chart_type):
        if self.show:
            cfields = self.get_fields(chart_type)
            self.sel_fields.options = cfields            
            try:
                self.out_url.clear_output()
                with self.out_url:  
                    print("%s - %s" %(self.all_charts[chart_type]['name'], self.all_charts[chart_type]['url']))
            except:
                print("URL Print error")

            try:
                self.out_func.clear_output()
                func_chunks = self.format_func(self.all_charts[chart_type]['func'], 120)
                with self.out_func:
                    for c in func_chunks:
                        print(c)
            except:
                print("Func print error")



    def format_func(self, out, mysize=100):
        fake_cur = out.find("(")
        cur = 0
        tlen = len(out)
        chunks = []
        next_comma = 0
        first = False
        while cur < tlen:
            if first == False:
                comma_search_start = fake_cur + mysize
            else:
                comma_search_start = cur + mysize
            next_comma = out[comma_search_start:].find(",")
            if next_comma >= 0:
                if first == False:
                    chunk = out[cur:next_comma + mysize + fake_cur + 1]
                else:
                    chunk = out[cur:next_comma + mysize + cur + 1]
                chunks.append(chunk)
                if first == False:
                    cur = fake_cur + mysize + next_comma + 1
                    first = True
                else:
                    cur = cur + mysize + next_comma + 1
            else:
                chunk = out[cur:]
                chunks.append(chunk)
                cur = tlen
        return chunks


    def df_change(self, change):
        if change['name'] == 'value':
            try:
                self.ourdf = self.ipy.user_ns[change['new']]
                self.sel_cols.options = self.ourdf.columns.tolist()
            except:
                if self.show:
                    with self.out_graph:
                        print("Error changing to %s" % change['new'])

    def get_fields(self, chart):
        exclude_list = ['title', 'width', 'height', 'data_frame']
        for e in self.opts['plotly_custom_exclude_list'][0]:
            exclude_list.append(e)

        func = self.all_charts[chart]['func']
        fields = func.split("(")[1].replace(")", "").replace("\n", "")
        arfields = [x.strip() for x in fields.split(",")]
        aritems = [z.split("=")[0] for z in arfields]
        arfiltered = [z for z in aritems if z not in exclude_list]

        return arfiltered






    def get_charts(self, refresh_charts=False):

        user_path = ""
        try:
            user_path = os.environ['HOME']
        except:
            if self.debug:
                print("No HOME Env Variable")
        if user_path == "":
            try:
                user_path = os.environ['USERPROFILE']
            except:
                if self.debug:
                    print("No HOME or USERPROFILE variables")
        if user_path == "":
            user_path = "."

       
        use_cache = self.opts['plotly_doc_cache_enabled'][0]
        cache_file = user_path + self.opts['plotly_doc_cache_file'][0]
        chart_dict = None
        get_docs = False
        if use_cache:
            if self.debug:
                print("Trying to load from %s" % cache_file)
            try:
                with open(cache_file, 'rb') as f:
                    chart_dict = pickle.load(f)
                if self.debug:
                    print("Success: Load from %s" % cache_file)
            except:
                if self.debug:
                    print("Could not load cache from %s" % cache_file)
                get_docs = True
        else:
            get_docs = True
        if refresh_charts == True:
            get_docs = True

        if get_docs == True:        
            if self.debug:
                print("Getting plotly docs from online")
            base_url = "https://plotly.com/python-api-reference/"
            api_ref = requests.get(base_url)
            if api_ref.status_code == 200:
                data = api_ref.text
            soup = BeautifulSoup(data, 'xml')

            refdiv = soup.find("div", {"id": "full-reference-list"})
            hrefs = refdiv.find_all('a')
            chart_dict = {}
            for a in hrefs:
                myhref = a["href"]
                mytext = a.get_text()
                if mytext.find("plotly.express.") == 0 and mytext.find("package") < 0:
                    mychart = mytext.replace("plotly.express.", "")
                    myurl = base_url + myhref
                    chtml = requests.get(myurl)
                    cdata = None
                    myfunc = ""
                    if chtml.status_code == 200:
                        cdata = chtml.text
                    if cdata is not None:
                        csoup = BeautifulSoup(cdata, 'xml')
                        dt = csoup.find("dt", {"id": mytext})
                        myfunc = dt.get_text()[0:-1]
                    chart_dict[mychart] = {"name": mytext, "url": myurl, "func": myfunc.strip()}

        if get_docs and use_cache:
            if self.debug:
                print("Saving Pickled Chart docs")
            # This means we had to get the docs, and we want to use the cash, so we save the results
            with open(cache_file, 'wb') as f:
                pickle.dump(chart_dict, f, pickle.HIGHEST_PROTOCOL)
        return chart_dict


##### setvar should only exist in the base_integration
    def setvar(self, line):

        allowed_opts = self.base_allowed_set_opts

        tline = line.replace('set ', '')
        tkey = tline.split(' ')[0] # Keys can't have spaces, values can
        tval = tline.replace(tkey + " ", "")
        if tval == "False":
            tval = False
        if tval == "True":
            tval = True
        if tkey in allowed_opts:
            self.opts[tkey][0] = tval
        else:
            print("You tried to set variable: %s - Not in Allowed options!" % tkey)

