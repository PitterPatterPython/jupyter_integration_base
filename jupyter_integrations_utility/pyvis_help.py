from IPython.display import IFrame
#from pyvis.network import Network
import pyvis.network
import pyvis
import os
import warnings
import hashlib
import datetime

def graph_pyvis_network(nodes, edges, directed=False, out_file="pyvis_output.html", nbdisplay=False, filter_menu=False, toggle_physics=True, buttons=[''], width=1800, height=1000, debug=False):
    """{"name": "graph_pyvis_network", 
         "desc": "Take a list of nodes and a list of edges and graph them with pyvis.",
         "return": "In addition to the html file with the pyvis output, also return a pyvis object", 
         "examples": [["mypyvis = graph_pyvis_network(nodes, edges)", "Graph nodes and edges"]
         ], 
         "args": [{"name": "nodes", "default": "None", "required": "True", "type": "list", "desc": "List of nodes with any sort of node formating"},
                  {"name": "edges", "default": "None", "required": "True", "type": "list", "desc": "List of edges with any sort of edge formating"},
                  {"name": "directed", "default": "False", "required": "False", "type": "boolean", "desc": "Show arrows on edges to show direction"},
                  {"name": "out_file", "default": "pyvis_output.html", "required": "False", "type": "string", "desc": "Default filename of the output. Will automatically overwrite and be stored in the same directory as the notebook"},
                  {"name": "nbdisplay", "default": "False", "required": "False", "type": "boolean", "desc": "Display in Notebook as well as write to html file"},
                  {"name": "filter_menu", "default": "False", "required": "False", "type": "boolean", "desc": "Not really sure yet"},
                  {"name": "toggle_physics", "default": "True", "required": "False", "type": "boolean", "desc": "When opoening HTML (in browser or notebook) should physicas automatically be calculated. Takes a lot of time on big graphs"},
                  {"name": "buttons", "default": "['']", "required": "False", "type": "list", "desc": "List of widgets to add to the html output. We've seen physics as the most common"},
                  {"name": "width", "default": "1800", "required": "False", "type": "integer", "desc": "Number of pixels to use as the width for the graph"},
                  {"name": "height", "default": "1000", "required": "False", "type": "integer", "desc": "Number of pixels to use as the height for the graph"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Formatting happens outside of this function. "]
         }
    """ 

#mynet = Network(height="1000px", bgcolor="#222222", font_color="white", filter_menu=True, notebook=True)

    str_width = f"{width}px"
    str_height = f"{height}px"

    print(f"Graphing Network with {len(nodes)} nodes and {len(edges)} edges")
#    buttons = ['nodes', 'edges', 'physics', 'layout', 'interaction', 'manipulation', 
    out_dir = os.getcwd()

    mynet = pyvis.network.Network(width=str_width, height=str_height, directed=directed, filter_menu=filter_menu, notebook=False)
    for n in nodes:
        try:
            mynet.add_node(n['id'], **n)
        except:
            print(n)
    #mynet.add_node(k, label=v['label'], color=v['color'], title=v['title'])
    for e in edges:
        tedge = e.copy()
        tfrom = tedge['from']
        tto = tedge['to']
        del tedge['from']
        del tedge['to']
        del tedge['id']
        mynet.add_edge(tfrom, tto, **tedge)
    mynet.toggle_physics(toggle_physics)
    mynet.show_buttons(filter_=buttons)
    full_path = f"{out_dir}\\{out_file}"
    mynet.save_graph(out_file)
    #mynet.generate_html(name=out_file, local=False, notebook=True)
#    mynet.show(out_file, local=False)
    print(f"Output to {full_path}")
    if nbdisplay:
        display(IFrame(out_file, width=width+200, height=height+200))
    return mynet


def color_2_htmlcol(colorname, default_color=None, debug=False):
    """{"name": "color_2_htmlcol", 
         "desc": "Convert a list of colors to HTML colors",
         "return": "Html Color of provided color or just return the color if not in list unless default_color is specified", 
         "examples": [["Used in calling of graph_network", "Most basic call"]
         ], 
         "args": [{"name": "colorname", "default": "None", "required": "True", "type": "string", "desc": "Color to convert to HTML"},
                  {"name": "default_color", "default": "None", "required": "False", "type": "string or None", "desc": "If a color is provided use this as the default html color otherwise return the string passed in (when None)"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Only a basic list as a helper"]
         }
    """    
    hcol = {
                    "Black": "#000000",
                    "Blue": "#0000FF",
                    "Gray": "#808080",
                    "Green": "#00FF00", # Wells
                    "Spring_Green": "#00FF7F",
                    "Purple": "#800080", #Citi
                    "Maroon": "#800000",
                    "Red": "#FF0000",    # BAC
                    "Coral": "#FF7F50",
                    "Orange": "#FFA500",
                    "White": "#FFFFFF",
                    "Yellow": "#FFFF00",
                    "Gold": "#FFD700", # PNC
                    "Pink": "#FF69B4",
                    "Deep_Pink": "#FF1493", 
                    "Magenta": "#FF00FF",
                    "Teal": "#00FFFF", # Huntington
                    "Honey_Dew": "#F0FFF0", # Ally
                    "Pale_Blue": "#AFEEEE", # US Bank
                    "Light_Purple": "#BB8FCE", #Truist
                    "Light_Blue": "#1E90FF" # Chase
                }
    retval = colorname
    if colorname not in hcol:
        if default_color is not None and default_color in hcol:
            retval = hcol[default_color]
            if debug:
                print(f"Color provided {colorname} not in color_list, using provided default color {default_color}")
        else:
            print(f"Default color provided not in color list: color provided: {colorname} not in color list - default_color provided: {default_color} also not in color list")
    else:
        retval = hcol[colorname]
        
    return retval
    
def ret_bank_cols(bank_str_format="zelle", debug=False):
    """{"name": "ret_bank_cols", 
         "desc": "Locked in colors for certain banks based on the string to keep visuals consistent",
         "return": "A dict of colors to send to color_basic function", 
         "examples": [["col_dict = ret_bank_cols()", "Returns Zelle Bank to Color List by default"]
         ], 
         "args": [{"name": "bank_str_format", "default": "zelle", "required": "False", "type": "string", "desc": "Format of strings, defaults to three letter codes for zelle"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Knowing how to send data into this function is important"]
         }
    """
    col_dict = {}
    if debug:
        print(f"Bank Code: {bank_str_format}")
    if bank_str_format == "zelle":
        col_dict={"JPM":"Light_Blue", "WFC":"Green", "CTI": "Purple", "H50": "Teal", "PNC": "Gold", "BAC": "Red", "ALB": "Honey_Dew", "BBT": "Light_Purple", "USB": "Pale_Blue"}
    else:
        print(f"Unknown bank_str_format {bank_str_format} - Currently supported: zelle")
    return col_dict


def node_or_edge_format(srcnodeoredge, format_map=None, default_node_format={"color": "#000000", "size": 30, "shape":"dot"}, default_edge_format={"color": "#000000"}, first_hit=True, always_use_default=False, matchlen=3, debug=False):
    """{"name": "node_or_edge_format", 
         "desc": "Provide a method to format nodes and edges based on string matching of the id",
         "return": "A node or edge dictionary with the formatting added if needed", 
         "examples": [["col_dict = ret_bank_cols()", "Returns Zelle Bank to Color List by default"]
         ], 
         "args": [{"name": "nodeoredge", "default": "", "required": "True", "type": "dict", "desc": "Dictionary of a node or edge. Must have an id column at a minimum"},
                  {"name": "format_map", "default": "None", "required": "False", "type": "dict or None", "desc": "Dictionary that has a key of a match string and value of a format dictionary. If None, nothing is added to the node"},
                  {"name": "default_node_format", "default": "{'color': 'Black', 'size': 30, 'shape':'dot'}", "required": "False", "type": "dict", "desc": "If a match occurs, and a certain item is not included this is the default for a node"},
                  {"name": "default_edge_format", "default": "{'color': 'Black'}", "required": "False", "type": "dict", "desc": "If a match occurs, and a certain item is not included this is the default for a edge"},
                  {"name": "first_hit", "default": "True", "required": "False", "type": "Bool", "desc": "Uses the first hit in a format_map. If False, uses the last hit in the format map"},
                  {"name": "always_use_default", "default": "False", "required": "False", "type": "Bool", "desc": "If there is not a hit on the format_map, still use the node or edge defaults. Defaults to False which just returns the node with no formating added."},
                  {"name": "matchlen", "default": "3", "required": "False", "type": "integer", "desc": "How much of the ID we should check against the format map"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": [""]
         }
    """
    
    nodeoredge = srcnodeoredge.copy()
    if format_map is None:
        return nodeoredge # If no dict is provided, don't even add the defaults

    
    
    
    if "source" in nodeoredge:
        format_type = "edge"
    else:
        format_type = "node"
    
    
    fullid = nodeoredge['id']
    matchid = fullid[0:matchlen]
    format_dict = None
    if format_type == "edge":
        format_dict = default_edge_format.copy()
    else:
        format_dict = default_node_format.copy()
    
    hit_dict = format_dict
    for m in format_map.keys():
        if debug:
            print(f"ID: {fullid}")
            print(f"Match ID: {matchid}")
            print(f"Match Key: {m}")
            
        if m[0] == "~":
            full_match = m.replace("~", "")
            if fullid.find(full_match) >= 0:
                hit_dict = format_map[m].copy()
                if first_hit:
                    break
        elif m.find(matchid) >= 0:
            hit_dict = format_map[m].copy()
            if first_hit:
                break
    if hit_dict is not None:
        format_dict.update(hit_dict)
        nodeoredge.update(format_dict)
    else:
        if always_use_default:
            nodeoredge.update(format_dict)
    return nodeoredge
    
