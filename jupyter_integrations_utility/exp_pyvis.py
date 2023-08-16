def get_login_nodes_edges(login_graph_df,  debug=False):
    """{"name": "get_login_nodes_edges", 
         "desc": "From the dataframe of formatted logins, produce two lists of nodes and edges",
         "return": "A tuple that is nodes and edges for the graph. (in that order)", 
         "examples": [["login_nodes, login_edges = get_login_nodes_edges(login_graph_df)", "Nodes and edges for get_logins_graph"]
         ], 
         "args": [{"name": "login_graph_df", "default": "None", "required": "True", "type": "pd.DataFrame", "desc": "Dataframe that is the result of the get_logins_graph function from pyvis_helper"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": ["Data must come from pyvis get_logins_graph"]
         }
    """      
    #process source nodes
    node_dict = {}
    out_srcs = login_graph_df.groupby(by=['src_id']).agg(num_logins=('num_logins', 'sum'), first_seen=('first_seen', 'min'), last_seen=('last_seen', 'max'),                                                         
                                                                names=('cust_name', lambda x: list(set(x))), onlineids=('cust_onlineid', lambda x: list(set(x))), pids=('cust_party_id', lambda x: list(set(x))),
                                                                num_targets=('tar_id', 'nunique')).reset_index()
    for i, r in out_srcs.iterrows():
        myid = r['src_id']
        num_logins = r['num_logins']
        first_seen = r['first_seen']
        last_seen = r['last_seen']
        names = r['names']
        onlineids = r['onlineids']
        pids = r['pids']
        num_targets = r['num_targets']
        mytitle = f"{myid}\nNumber of Logins:{num_logins}\nFirst Seen: {first_seen}\nLast Seen: {last_seen}\nNumber of Target Nodes:{num_targets}\nOnline IDs:{onlineids}\nNames: {names}\nPIDs:{pids}\n"
        tdict = {"label": myid, "title": mytitle}
        node_dict[myid] = tdict

    # process target nodes
    out_dsts = login_graph_df.groupby(by=['tar_id']).agg(num_logins=('num_logins', 'sum'), first_seen=('first_seen', 'min'), last_seen=('last_seen', 'max'),                                                         
                                                                names=('cust_name', lambda x: list(set(x))), onlineids=('cust_onlineid', lambda x: list(set(x))), pids=('cust_party_id', lambda x: list(set(x))),
                                                                num_sources=('src_id', 'nunique')).reset_index()
    for i, r in out_dsts.iterrows():
        myid = r['tar_id']
        num_logins = r['num_logins']
        first_seen = r['first_seen']
        last_seen = r['last_seen']
        names = r['names']
        onlineids = r['onlineids']
        pids = r['pids']
        num_sources = r['num_sources']
        mytitle = f"{myid}\nNumber of Logins:{num_logins}\nFirst Seen: {first_seen}\nLast Seen: {last_seen}\nNumber of Source Nodes:{num_sources}\nOnline IDs:{onlineids}\nNames: {names}\nPIDs:{pids}\n"
        tdict = {"label": myid, "title": mytitle}
        node_dict[myid] = tdict        
            
    node_list = []
    for myid in node_dict.keys():
        tdict = node_dict[myid].copy()
        tdict['id'] = myid
        node_list.append(tdict)

  

    # Process Edges
    edge_list = []
    out_edges = login_graph_df.groupby(by=['src_id', 'tar_id']).agg(total_logins=('num_logins', 'sum'),  first_seen=('first_seen', 'min'), last_seen=('last_seen', 'max')).reset_index()
   
    for i, r in out_edges.iterrows():
        mysrc = r['src_id']
        mytar = r['tar_id']
        fseen = r['first_seen']
        lseen = r['last_seen']
        total_logins = r['total_logins']
        weight = total_logins
        myid = f"{mysrc}~{mytar}"
        mytitle = f"Total Logins: {total_logins}\nFirst Seen: {fseen}\nLast Seen: {lseen}\n"
        edge_list.append({"from": mysrc, "to": mytar, "id":myid, "title": mytitle, "weight": weight})

    return node_list, edge_list

def format_login_edges_nodes(login_nodes, login_edges, seed_pids=[], debug=False):
    """{"name": "format_login_edges_nodes", 
         "desc": "Take two lists of nodes and edges and format them per login items. Using seed_accts put stars to identify what started things",
         "return": "A tuple that is formatted nodes and edges for the graph. (in that order)", 
         "examples": [["login_formatted_nodes, login_formatted_edges = format_login_edges_nodes(login_nodes, login_edges)", "Nodes and edges for Logins Graph"]
         ], 
         "args": [{"name": "logins_nodes", "default": "None", "required": "True", "type": "list", "desc": "List of nodes used in login graph"},
                  {"name": "login_edges", "default": "None", "required": "True", "type": "list", "desc": "List of edges used in login graph"},
                  {"name": "seed_accts", "default": "[]", "required": "False", "type": "list", "desc": "List of accts and/or tokens that are the seeds for highlighting"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": []
         }
    """    
    formatted_nodes = []
    formatted_edges = []
    login_seed_format = {'size':50, 'borderWidth':10, 'shape': "star"} # Need to work on this
    #raw_node_color_map = ret_bank_cols()
    node_color_map = {}
    #for x in raw_node_color_map.keys():
    #    node_color_map[x] = {"color":  color_2_htmlcol(raw_node_color_map[x])}


    node_color_map['COOK'] = {"color":  color_2_htmlcol("Red")} 
    if debug:
        print(node_color_map)
    for x in login_nodes:
        temp_node = node_or_edge_format(x, format_map=node_color_map, matchlen=4, debug=debug)
        for x in seed_pids:
            if temp_node['id'].find(x) >= 0:
                temp_node.update(login_seed_format)
                break
        formatted_nodes.append(temp_node)
        temp_node = None
#        formatted_nodes.append(node_or_edge_format(x, format_map=node_color_map, debug=debug))
    
    for x in login_edges:
        formatted_edges.append(node_or_edge_format(x, format_map=None))
        
    return formatted_nodes, formatted_edges 
