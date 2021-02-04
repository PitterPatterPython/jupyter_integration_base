#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
import asyncio
from pathlib import Path
from collections import OrderedDict
import requests
from copy import deepcopy
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Javascript, FileLink, FileLinks, Image
import pandas as pd
# Widgets
from ipywidgets import GridspecLayout, widgets

# Requests and BeutifulSoup
try:
    from bs4 import BeautifulSoup
except:
    print("Could not import BeutifulSoup")

# Pickle
try:
    import pickle
except:
    print("Could not import pickle")

try:
    import plotly.graph_objects as go
    import plotly.express as px
except:
    print("Error loading plotly")

from addon_core import Addon

@magics_class
class Vis(Addon):
    # Static Variables

    magic_name = "vis"
    name_str = "vis"

    ourdf = None            # The df we are working with
    all_charts = None       # Chart doc data
    show = False            # Should we write output

    custom_evars = []

    input_watch_running = False

    last_chart_code = ""

    custom_allowed_set_opts = ['vis_search_prefix']

    myopts = {}
    myopts['vis_search_prefix'] = ["prev_", "The Variable prefix to look for when showing availble dataframes"]
    myopts['vis_plotly_doc_cache_enabled'] = [True, "Use a cache file for plotly"]
    myopts['vis_addon_dir'] = ['~/.ipython/integrations/' + name_str, "Directory for Visualization caching/configs"]
    myopts['vis_plotly_doc_cache_file'] = ["plotly_doc.pkl", "A cache file to speed up lookups - TEMP"]
    myopts['vis_plotly_custom_exclude_list'] = [[], "A list of fields that show up in plotly functions that you may want to exclude in the vis widgets - Comma sep values here, no spaces"] 

    avail_dfs = []
    height = ""
    width = ""
    bDisplayed = False
    inc_indexes = False
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
    chk_incidx = None
    lbl_fields = None
    lbl_assigned = None

    sel_cols = None
    sel_fields = None
    sel_assigned = None

    sel_df = None
    drp_charts = None





    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables.
    def __init__(self, shell, debug=False, width="1500px", height="750px", *args, **kwargs):
        super(Vis, self).__init__(shell, debug=debug)
        self.debug = debug
        self.width = width
        self.height = height


        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)
        shell.user_ns['vis_var'] = self.creation_name
        # Run the Plotly code in the user_ns
        runcode = "try:\n    import plotly.graph_objects as go\n    import plotly.express as px\nexcept:\n    pass\n"
        shell.ex(runcode)

        try:
            a = type(pickle)
        except:
            print("Pickle not installed, caching won't work")


        self.all_charts = self.get_charts()

        try:
            a = type(px)
        except:
            print("Plotly, and plotly express doesn't seem to be installed - This will cause problems for a plotly based visualization helper")
        try:
            a = type(BeautifulSoup)
        except:
           print("You need BeautifulSoup - make sure this is installed")




    def showVisWidget(self, line):
        if self.bDisplayed == False:
            self.instantiate_objects()
            self.fill_widgets()
            self.layout_grid()
            self.bDisplayed = True
        self.refresh_avail_dfs()

        if line == "" :
            pass
        else:
            if line.strip() != "vis":
                self.avail_dfs.append(line)

        self.sel_df.options = self.avail_dfs
        self.show = True
        self.drp_charts.value = "line"
        self.set_vis("line")
        self.update_columns(self.sel_df.value)
        self.show = True
#        if self.debug:
#            print("Starting watch before async submission")
#        if self.input_watch_running == False:
#            asyncio.create_task(self.check_and_set_next_chart_input("nextinput"), name="nextinput")
#            self.input_watch_running = True
#        else:
#            print("Can't start next input watcher due to it already running")
        display(self.dg)

#    async def check_and_set_next_chart_input(self, taskname):
#        if self.debug:
#            print("In Watch thread - started")
#        myvar = 0
#        sleeptime = 1
#        while True:
#            myvar += sleeptime
#            if self.debug:
#                print("Loop: %s" % myvar)

#            if self.last_chart_code != "":
#                for task in asyncio.all_tasks():
#                    if task.get_name() == taskname:
#                        mytask = task
#                        break
#                mytask.cancel()
#                self.ipy.set_next_input(self.last_chart_code)
#                self.last_chart_code = ""
#                self.input_watch_running = False

 #           await asyncio.sleep(sleeptime)

#        if self.debug:
#            print("We are done now: %s" % self.last_chart_code)


    # This is the magic name.
    @line_cell_magic
    def vis(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            if line is None or line.strip() == "":
                line = "vis"
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations. 
                if line.lower().find("vis") == 0:
                    newline = line.replace("vis ", "").strip()
                    self.showVisWidget(newline)
                elif line.strip().split(" ")[0] in self.ipy.user_ns:
                    self.vis("vis " + line.strip())
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)

    def customStatus(self):
        # Todo put in information about the persisted information
        print("Vis Addon Subsystem: Installed")


# Display Help can be customized
    def customHelp(self):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m

        curoutput = self.displayAddonHelp()
        curoutput += "\n"
        curoutput += "Visulaization Helper Functions\n"
        curoutput += "\n"
        curoutput += "This addon helps to facilitate Visualizations within your Jupyter Notebooks"
        curoutput += "\n"
        curoutput += "{: <35} {: <80}\n".format(*[m, "Bring up Visualization Widget for all dataframes that start with " + self.opts['vis_search_prefix'][0] ])
        curoutput += "{: <35} {: <80}\n".format(*[m + " <yourdf>", "Bring up Visualization Widget, but add in your custom dataframe yourdf"])
        curoutput += "\n"

        return curoutput


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
        self.dg[4, 3] = self.chk_incidx
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

    def chk_index(self, change):
        if change['name'] == 'value':
            self.inc_indexes = change['new']
            self.update_columns(self.sel_df.value)

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
        self.chk_incidx.observe(self.chk_index)
        self.btn_gen.on_click(self.gen_vis)
        self.btn_add.on_click(self.add_mapping)
        self.btn_rem.on_click(self.rem_mapping)
        self.btn_clear_assigned.on_click(self.clear_assigned)

    def clear_assigned(self, b):
        self.sel_assigned.options = []

    def add_mapping(self, b):
        mycol = ""
        myfield = ""
        col_quotes = True
        mycol = self.sel_cols.value
        myfield = self.sel_fields.value
        if mycol.find(".index") >=1:
            col_quotes = False
        if mycol != "" and myfield != "":
            if col_quotes:
                myassigned = myfield + '="' + mycol + '"'
            else:
                myassigned = myfield + '=' + mycol

            curopts = deepcopy(list(self.sel_assigned.options))
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
        self.chk_incidx = widgets.Checkbox(value=False, description='Inc. Index', disabled=False, indent=False)
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

        chk_dict = {}
        for x in assigned:
            l = x.split("=")
            if l[0] in chk_dict:
                chk_dict[l[0]].append(l[1])
            else:
                chk_dict[l[0]] = [l[1]]

        for k in chk_dict.keys():
            if len(chk_dict[k]) == 1:
                v = chk_dict[k][0]
                if v.find(".index") >= 1:
                    out += k + " = [" + chk_dict[k][0] + "], "
                else:
                    out += k + " = " + self.sel_df.value + "[" + chk_dict[k][0] + "], "
            else:
                out += k + " = ["
                for i in chk_dict[k]:
                    if i.find(".index") >= 1:
                        out += i + ", "
                    else:
                        out += self.sel_df.value + "[" + i + "], "
                out = out[0:-2] + "], "

    #    for a in assigned:
    #        out+= a + ", "
        out = out[0:-2] + ")"
        my_chart_code = "fig = " + out + "\nfig.show()"
        if self.show:
            try:
                self.out_graph.clear_output()
                with self.out_graph:
                    print(my_chart_code)
            except:
                print("Out graph error")
        self.last_chart_code = my_chart_code



    # I wish this worked
    # Maybe threading to check for a value?
    #     self.ipy.set_next_input("fig = " + out + "\nfig.show()") # Doesn't work until the NEXT cell is run. 



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

    def update_columns(self, df_name):
        try:
            addar = []
            self.ourdf = self.ipy.user_ns[df_name]
            if self.inc_indexes == True:
                addar = [df_name + ".index"]
            self.sel_cols.options = addar + self.ourdf.columns.tolist()
        except:
            if self.show:
                with self.out_graph:
                    print("Error changing to %s" % df_name)

    def df_change(self, change):
        if change['name'] == 'value':
            new_df = change['new']
            self.update_columns(new_df)

    def get_fields(self, chart):
        exclude_list = ['title', 'width', 'height', 'data_frame']
        for e in self.opts['vis_plotly_custom_exclude_list'][0]:
            exclude_list.append(e)

        func = self.all_charts[chart]['func']
        fields = func.split("(")[1].replace(")", "").replace("\n", "")
        arfields = [x.strip() for x in fields.split(",")]
        aritems = [z.split("=")[0] for z in arfields]
        arfiltered = [z for z in aritems if z not in exclude_list]

        return arfiltered

    def get_charts(self, refresh_charts=False):

        tstorloc = self.opts['vis_addon_dir'][0]
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
        self.vis_dir = tpdir

        if not os.path.isdir(self.vis_dir):
            os.makedirs(self.vis_dir)
        cache_file = self.vis_dir / self.opts['vis_plotly_doc_cache_file'][0]
        use_cache = self.opts['vis_plotly_doc_cache_enabled'][0]

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
            try:
                api_ref = requests.get(base_url)
                mycode = api_ref.status_code
            except:
                mycode = 500

            if mycode == 200:
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
            else:
                print("HTTP connection to get current plotly docs errored out - using static list which may be outdated")
                chart_dict = self.ret_static_charts()

        if get_docs and use_cache:
            if self.debug:
                print("Saving Pickled Chart docs")
            # This means we had to get the docs, and we want to use the cash, so we save the results
            with open(cache_file, 'wb') as f:
                pickle.dump(chart_dict, f, pickle.HIGHEST_PROTOCOL)
        return chart_dict



    def ret_static_charts(self):
        scharts = """{'scatter': {'name': 'plotly.express.scatter', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.scatter.html', 'func': "plotly.express.scatter(data_frame=None, x=None, y=None, color=None, symbol=None, size=None, hover_name=None, hover_data=None, custom_data=None, text=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, error_x=None, error_x_minus=None, error_y=None, error_y_minus=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, orientation=None, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, symbol_sequence=None, symbol_map={}, opacity=None, size_max=None, marginal_x=None, marginal_y=None, trendline=None, trendline_color_override=None, log_x=False, log_y=False, range_x=None, range_y=None, render_mode='auto', title=None, template=None, width=None, height=None)"}, 'scatter_3d': {'name': 'plotly.express.scatter_3d', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.scatter_3d.html', 'func': 'plotly.express.scatter_3d(data_frame=None, x=None, y=None, z=None, color=None, symbol=None, size=None, text=None, hover_name=None, hover_data=None, custom_data=None, error_x=None, error_x_minus=None, error_y=None, error_y_minus=None, error_z=None, error_z_minus=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, size_max=None, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, symbol_sequence=None, symbol_map={}, opacity=None, log_x=False, log_y=False, log_z=False, range_x=None, range_y=None, range_z=None, title=None, template=None, width=None, height=None)'}, 'scatter_polar': {'name': 'plotly.express.scatter_polar', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.scatter_polar.html', 'func': "plotly.express.scatter_polar(data_frame=None, r=None, theta=None, color=None, symbol=None, size=None, hover_name=None, hover_data=None, custom_data=None, text=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, symbol_sequence=None, symbol_map={}, opacity=None, direction='clockwise', start_angle=90, size_max=None, range_r=None, range_theta=None, log_r=False, render_mode='auto', title=None, template=None, width=None, height=None)"}, 'scatter_ternary': {'name': 'plotly.express.scatter_ternary', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.scatter_ternary.html', 'func': 'plotly.express.scatter_ternary(data_frame=None, a=None, b=None, c=None, color=None, symbol=None, size=None, text=None, hover_name=None, hover_data=None, custom_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, symbol_sequence=None, symbol_map={}, opacity=None, size_max=None, title=None, template=None, width=None, height=None)'}, 'scatter_mapbox': {'name': 'plotly.express.scatter_mapbox', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.scatter_mapbox.html', 'func': 'plotly.express.scatter_mapbox(data_frame=None, lat=None, lon=None, color=None, text=None, hover_name=None, hover_data=None, custom_data=None, size=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, opacity=None, size_max=None, zoom=8, center=None, mapbox_style=None, title=None, template=None, width=None, height=None)'}, 'scatter_geo': {'name': 'plotly.express.scatter_geo', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.scatter_geo.html', 'func': 'plotly.express.scatter_geo(data_frame=None, lat=None, lon=None, locations=None, locationmode=None, color=None, text=None, hover_name=None, hover_data=None, custom_data=None, size=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, opacity=None, size_max=None, projection=None, scope=None, center=None, title=None, template=None, width=None, height=None)'}, 'line': {'name': 'plotly.express.line', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.line.html', 'func': "plotly.express.line(data_frame=None, x=None, y=None, line_group=None, color=None, line_dash=None, hover_name=None, hover_data=None, custom_data=None, text=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, error_x=None, error_x_minus=None, error_y=None, error_y_minus=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, orientation=None, color_discrete_sequence=None, color_discrete_map={}, line_dash_sequence=None, line_dash_map={}, log_x=False, log_y=False, range_x=None, range_y=None, line_shape=None, render_mode='auto', title=None, template=None, width=None, height=None)"}, 'line_3d': {'name': 'plotly.express.line_3d', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.line_3d.html', 'func': 'plotly.express.line_3d(data_frame=None, x=None, y=None, z=None, color=None, line_dash=None, text=None, line_group=None, hover_name=None, hover_data=None, custom_data=None, error_x=None, error_x_minus=None, error_y=None, error_y_minus=None, error_z=None, error_z_minus=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, line_dash_sequence=None, line_dash_map={}, log_x=False, log_y=False, log_z=False, range_x=None, range_y=None, range_z=None, title=None, template=None, width=None, height=None)'}, 'line_polar': {'name': 'plotly.express.line_polar', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.line_polar.html', 'func': "plotly.express.line_polar(data_frame=None, r=None, theta=None, color=None, line_dash=None, hover_name=None, hover_data=None, custom_data=None, line_group=None, text=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, line_dash_sequence=None, line_dash_map={}, direction='clockwise', start_angle=90, line_close=False, line_shape=None, render_mode='auto', range_r=None, range_theta=None, log_r=False, title=None, template=None, width=None, height=None)"}, 'line_ternary': {'name': 'plotly.express.line_ternary', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.line_ternary.html', 'func': 'plotly.express.line_ternary(data_frame=None, a=None, b=None, c=None, color=None, line_dash=None, line_group=None, hover_name=None, hover_data=None, custom_data=None, text=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, line_dash_sequence=None, line_dash_map={}, line_shape=None, title=None, template=None, width=None, height=None)'}, 'line_mapbox': {'name': 'plotly.express.line_mapbox', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.line_mapbox.html', 'func': 'plotly.express.line_mapbox(data_frame=None, lat=None, lon=None, color=None, text=None, hover_name=None, hover_data=None, custom_data=None, line_group=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, zoom=8, center=None, mapbox_style=None, title=None, template=None, width=None, height=None)'}, 'line_geo': {'name': 'plotly.express.line_geo', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.line_geo.html', 'func': 'plotly.express.line_geo(data_frame=None, lat=None, lon=None, locations=None, locationmode=None, color=None, line_dash=None, text=None, hover_name=None, hover_data=None, custom_data=None, line_group=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, line_dash_sequence=None, line_dash_map={}, projection=None, scope=None, center=None, title=None, template=None, width=None, height=None)'}, 'area': {'name': 'plotly.express.area', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.area.html', 'func': 'plotly.express.area(data_frame=None, x=None, y=None, line_group=None, color=None, hover_name=None, hover_data=None, custom_data=None, text=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, orientation=None, groupnorm=None, log_x=False, log_y=False, range_x=None, range_y=None, line_shape=None, title=None, template=None, width=None, height=None)'}, 'bar': {'name': 'plotly.express.bar', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.bar.html', 'func': "plotly.express.bar(data_frame=None, x=None, y=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, custom_data=None, text=None, base=None, error_x=None, error_x_minus=None, error_y=None, error_y_minus=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, opacity=None, orientation=None, barmode='relative', log_x=False, log_y=False, range_x=None, range_y=None, title=None, template=None, width=None, height=None)"}, 'timeline': {'name': 'plotly.express.timeline', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.timeline.html', 'func': 'plotly.express.timeline(data_frame=None, x_start=None, x_end=None, y=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, custom_data=None, text=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, opacity=None, range_x=None, range_y=None, title=None, template=None, width=None, height=None)'}, 'bar_polar': {'name': 'plotly.express.bar_polar', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.bar_polar.html', 'func': "plotly.express.bar_polar(data_frame=None, r=None, theta=None, color=None, hover_name=None, hover_data=None, custom_data=None, base=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, barnorm=None, barmode='relative', direction='clockwise', start_angle=90, range_r=None, range_theta=None, log_r=False, title=None, template=None, width=None, height=None)"}, 'violin': {'name': 'plotly.express.violin', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.violin.html', 'func': 'plotly.express.violin(data_frame=None, x=None, y=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, custom_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, orientation=None, violinmode=None, log_x=False, log_y=False, range_x=None, range_y=None, points=None, box=False, title=None, template=None, width=None, height=None)'}, 'box': {'name': 'plotly.express.box', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.box.html', 'func': 'plotly.express.box(data_frame=None, x=None, y=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, custom_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, orientation=None, boxmode=None, log_x=False, log_y=False, range_x=None, range_y=None, points=None, notched=False, title=None, template=None, width=None, height=None)'}, 'strip': {'name': 'plotly.express.strip', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.strip.html', 'func': 'plotly.express.strip(data_frame=None, x=None, y=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, custom_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, orientation=None, stripmode=None, log_x=False, log_y=False, range_x=None, range_y=None, title=None, template=None, width=None, height=None)'}, 'histogram': {'name': 'plotly.express.histogram', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.histogram.html', 'func': "plotly.express.histogram(data_frame=None, x=None, y=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, marginal=None, opacity=None, orientation=None, barmode='relative', barnorm=None, histnorm=None, log_x=False, log_y=False, range_x=None, range_y=None, histfunc=None, cumulative=None, nbins=None, title=None, template=None, width=None, height=None)"}, 'pie': {'name': 'plotly.express.pie', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.pie.html', 'func': 'plotly.express.pie(data_frame=None, names=None, values=None, color=None, color_discrete_sequence=None, color_discrete_map={}, hover_name=None, hover_data=None, custom_data=None, labels={}, title=None, template=None, width=None, height=None, opacity=None, hole=None)'}, 'treemap': {'name': 'plotly.express.treemap', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.treemap.html', 'func': 'plotly.express.treemap(data_frame=None, names=None, values=None, parents=None, ids=None, path=None, color=None, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, color_discrete_sequence=None, color_discrete_map={}, hover_name=None, hover_data=None, custom_data=None, labels={}, title=None, template=None, width=None, height=None, branchvalues=None, maxdepth=None)'}, 'sunburst': {'name': 'plotly.express.sunburst', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.sunburst.html', 'func': 'plotly.express.sunburst(data_frame=None, names=None, values=None, parents=None, path=None, ids=None, color=None, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, color_discrete_sequence=None, color_discrete_map={}, hover_name=None, hover_data=None, custom_data=None, labels={}, title=None, template=None, width=None, height=None, branchvalues=None, maxdepth=None)'}, 'funnel': {'name': 'plotly.express.funnel', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.funnel.html', 'func': 'plotly.express.funnel(data_frame=None, x=None, y=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, custom_data=None, text=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, opacity=None, orientation=None, log_x=False, log_y=False, range_x=None, range_y=None, title=None, template=None, width=None, height=None)'}, 'funnel_area': {'name': 'plotly.express.funnel_area', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.funnel_area.html', 'func': 'plotly.express.funnel_area(data_frame=None, names=None, values=None, color=None, color_discrete_sequence=None, color_discrete_map={}, hover_name=None, hover_data=None, custom_data=None, labels={}, title=None, template=None, width=None, height=None, opacity=None)'}, 'scatter_matrix': {'name': 'plotly.express.scatter_matrix', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.scatter_matrix.html', 'func': 'plotly.express.scatter_matrix(data_frame=None, dimensions=None, color=None, symbol=None, size=None, hover_name=None, hover_data=None, custom_data=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, symbol_sequence=None, symbol_map={}, opacity=None, size_max=None, title=None, template=None, width=None, height=None)'}, 'parallel_coordinates': {'name': 'plotly.express.parallel_coordinates', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.parallel_coordinates.html', 'func': 'plotly.express.parallel_coordinates(data_frame=None, dimensions=None, color=None, labels={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, title=None, template=None, width=None, height=None)'}, 'parallel_categories': {'name': 'plotly.express.parallel_categories', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.parallel_categories.html', 'func': 'plotly.express.parallel_categories(data_frame=None, dimensions=None, color=None, labels={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, title=None, template=None, width=None, height=None, dimensions_max_cardinality=50)'}, 'choropleth': {'name': 'plotly.express.choropleth', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.choropleth.html', 'func': 'plotly.express.choropleth(data_frame=None, lat=None, lon=None, locations=None, locationmode=None, geojson=None, featureidkey=None, color=None, hover_name=None, hover_data=None, custom_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, projection=None, scope=None, center=None, title=None, template=None, width=None, height=None)'}, 'choropleth_mapbox': {'name': 'plotly.express.choropleth_mapbox', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.choropleth_mapbox.html', 'func': 'plotly.express.choropleth_mapbox(data_frame=None, geojson=None, featureidkey=None, locations=None, color=None, hover_name=None, hover_data=None, custom_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_discrete_sequence=None, color_discrete_map={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, opacity=None, zoom=8, center=None, mapbox_style=None, title=None, template=None, width=None, height=None)'}, 'density_contour': {'name': 'plotly.express.density_contour', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.density_contour.html', 'func': 'plotly.express.density_contour(data_frame=None, x=None, y=None, z=None, color=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, orientation=None, color_discrete_sequence=None, color_discrete_map={}, marginal_x=None, marginal_y=None, trendline=None, trendline_color_override=None, log_x=False, log_y=False, range_x=None, range_y=None, histfunc=None, histnorm=None, nbinsx=None, nbinsy=None, title=None, template=None, width=None, height=None)'}, 'density_heatmap': {'name': 'plotly.express.density_heatmap', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.density_heatmap.html', 'func': 'plotly.express.density_heatmap(data_frame=None, x=None, y=None, z=None, facet_row=None, facet_col=None, facet_col_wrap=0, facet_row_spacing=None, facet_col_spacing=None, hover_name=None, hover_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, orientation=None, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, marginal_x=None, marginal_y=None, opacity=None, log_x=False, log_y=False, range_x=None, range_y=None, histfunc=None, histnorm=None, nbinsx=None, nbinsy=None, title=None, template=None, width=None, height=None)'}, 'density_mapbox': {'name': 'plotly.express.density_mapbox', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.density_mapbox.html', 'func': 'plotly.express.density_mapbox(data_frame=None, lat=None, lon=None, z=None, hover_name=None, hover_data=None, custom_data=None, animation_frame=None, animation_group=None, category_orders={}, labels={}, color_continuous_scale=None, range_color=None, color_continuous_midpoint=None, opacity=None, zoom=8, center=None, mapbox_style=None, radius=None, title=None, template=None, width=None, height=None)'}, 'imshow': {'name': 'plotly.express.imshow', 'url': 'https://plotly.com/python-api-reference/generated/plotly.express.imshow.html', 'func': 'plotly.express.imshow(img, zmin=None, zmax=None, origin=None, labels={}, x=None, y=None, color_continuous_scale=None, color_continuous_midpoint=None, range_color=None, title=None, template=None, width=None, height=None, aspect=None)'}}"""
        return eval(scharts)
