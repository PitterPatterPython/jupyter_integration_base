import re
import json
import datetime
import pandas as pd
import inspect
import numpy as np

def reapply_all(dfname="mydf", dfitem="zeropadded_accountnumber", featname="all_features", clausename="all_clauses", include_md=False):
    """ {"name": "reapply_all", 
         "desc": "Prints out the default reapply data for features and clauses",
         "return": "Prints the code in the next cell", 
         "examples": [["reapply_all()", "Prints feature reapply code in the next cell"]], 
         "args": [{"name": "dfname", "default": "mydf", "required": "False", "type": "string", "desc": "Name of the dataframe with data to calculate features against"},
                  {"name": "dfitem", "default": "zeropadded_accountnumber", "required": "False", "type": "string", "desc": "Name of item (typically account number)"},
                  {"name": "featname", "default": "all_features", "required": "False", "type": "string", "desc": "Name of features dict"},
                  {"name": "clausename", "default": "all_clauses", "required": "False", "type": "string", "desc": "Name of clauses list"},
                  {"name": "include_md", "default": "False", "required": "False", "type": "boolean", "desc": "Print the Markdown version as well as the dataframe version"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": []
        }
    """

    ipy = get_ipython()

    out_str = f"{dfname} = apply_features({dfname}, {featname}, rerun_apply=False, dry_run=False)\n"
    out_str += f"{dfname} = apply_custom_clauses({dfname}, {featname}, {clausename}, rerun_apply=False, dry_run=False, debug=False)\n"
    out_str += f"df_out = output_features({featname}, custom_clauses={clausename}, event_df={dfname}, calc_features=True, event_item='{dfitem}', "
    out_str += f"output_type='dataframe', md_output_header=None, display_features=None, display_groups=None, debug=False)\n"
    if include_md:
        out_str += f"md_out = output_features({featname}, custom_clauses={clausename}, event_df={dfname}, calc_features=True, event_item='{dfitem}', "
        out_str += f"output_type='markdown', md_output_header=None, display_features=None, display_groups=None, debug=False)\n"
    ipy.set_next_input(out_str)



def ret_var_name(var):
    """ {"name": "ret_var_name", 
         "desc": "For a given varible, get its original name",
         "return": "String name of the orignal variable", 
         "examples": [["myvarname = ret_var_name(a_var)", "Should return a_var, works well for lists of vars"]], 
         "args": [{"name": "var", "default": "NA", "required": "True", "type": "Any", "desc": "Original name of variable"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": []
        }
    """


    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]

def increase_date_window(dstart, dend, numdays):
    """ {"name": "increase_date_window",
         "desc": "Take a start and end date, and increse the number of days on either end",
         "return": "Datestart and dateend both increased by the number of days ", 
         "examples": ["trans_add_zelle = add_zelle_info_to_dda_trans(transdf, batchsize=1000, debug=False)"], 
         "args": [{"name": "dstart", "default": "NA", "required": "True", "type": "string", "desc": "Date start in %Y-%m-%d format"},
                  {"name": "dend", "default": "NA", "required": "True", "type": "string", "desc": "Date end in %Y-%m-%d format"},
                  {"name": "numdays", "default": "NA", "required": "True", "type": "integer", "desc": "Number of days to widen the window on each side"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": ["Format must by in %Y-%m-%d i.e. 2023-02-01 format"]
         }
    """
    window_dstart = (datetime.datetime.strptime(dstart, "%Y-%m-%d") - datetime.timedelta(days=numdays)).strftime("%Y-%m-%d")
    window_dend = (datetime.datetime.strptime(dend, "%Y-%m-%d") + datetime.timedelta(days=numdays)).strftime("%Y-%m-%d")
    return window_dstart, window_dend


def feature_compare(df_list, df_label, feat_dict, clause_list, event_item):
    """ {"name": "feature_compare", 
         "desc": "For a list of dataframe outputs from feature calculations (i.e. different populations) calculate features and return a dataframee that compares them",
         "return": "A feature comparison dataframe between the passed populations", 
         "examples": [["compare_out_df = feature_compare([all_apps, pre_mar1_apps, post_mar1_apps], '_apps', all_features, all_clauses, 'zeropadded_accountnumber')", "Compare three populations of apps, all, pre_mar1, post_mar1"]], 
         "args": [{"name": "df_list", "default": "NA", "required": "True", "type": "list of pd.DataFrame", "desc": "List of dataframes that have calculated features. These are different populations"},
                  {"name": "df_label", "default": "NA", "required": "True", "type": "string", "desc": "String that exists in each dataframe name. We remove this to get the population labels. Ex. _apps"},
                  {"name": "feat_dict", "default": "NA", "required": "True", "type": "dict", "desc": "Dictionary of features to apply to all populations"},
                  {"name": "clause_list", "default": "NA", "required": "True", "type": "list", "desc": "List of clauses to apply to all populations"},
                  {"name": "event_item", "default": "NA", "required": "True", "type": "string", "desc": "The uniq item. Often Account number, or session id. i.e zeropadded_accountnumber"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": ["The df_label is portion of the dataframe name that will be removed. What is remaining becomes the prefix for the output columns"]
        }
    """



    df_name_list = []
    calc_dfs = {}
    print(f"Hi - No. of DFs: {len(df_list)}")
    prefix_list = []
    for mydf in df_list:
        myname = ret_var_name(mydf)[-1]
        myprefix = myname.replace(df_label, "")
        prefix_list.append(myprefix)
        df_name_list.append(myname)
        print(f"Processing {myname}")
        this_df_out = output_features(feat_dict, custom_clauses=clause_list, event_df=mydf,
                                      calc_features=True, event_item=event_item, output_type='dataframe')
        this_df_out.rename(columns={"feature_count": f"{myprefix}_feature_count", "all_items": f"{myprefix}_all_items",
                                                   "feature_percentage": f"{myprefix}_feature_percentage"}, inplace=True)
   #     print(f"{this_df_out.columns.tolist()}")
        calc_dfs[myname] = this_df_out
        this_df_out = None

    merged_df = None
    col_list = ['display_group', 'feature', 'description']

    for mydf in df_name_list:
        #print(f"Merging {mydf}")
        if merged_df is None:
            merged_df = calc_dfs[mydf]
        else:
            merged_df = merged_df.merge(calc_dfs[mydf], on=['display_group', 'feature', 'description'])

    col_list = ['display_group', 'feature', 'description']
    col_counts = ['feature_percentage', 'feature_count', 'all_items']
    for col_cnt in col_counts:
        for p in prefix_list:
            col_list.append(f"{p}_{col_cnt}")
  #  print(col_list)
  #  print(f"{merged_df.columns.tolist()}")

    merged_df = merged_df[col_list]
    return merged_df


def apply_features(apply_df, feat_dict, rerun_apply=False, stop_on_fail=False, dry_run=False, debug=False, show_copy_errors=False):
    """ {"name": "apply_features", 
         "desc": "Take a dataframe of data, and apply features from a feature dictionary. Return the dataframe with the feature columns applied",
         "return": "Dataframe with applied features as columns", 
         "examples": ["mydf = apply_features(mydf, myfeatures)"], 
         "args": [{"name": "apply_df", "default": "NA", "required": "True", "type": "pd.DataFrame", "desc": "Dataframe of data to apply features to"},
                  {"name": "feat_dict", "default": "NA", "required": "True", "type": "dict", "desc": "Dictionary of features to apply"},
                  {"name": "rerun_apply", "default": "False", "required": "False", "type": "boolean", "desc": "If the column already exists, we don't apply the feature unless this is true"},
                  {"name": "stop_on_fail", "default": "False", "required": "False", "type": "boolean", "desc": "If a feature application has an exception, if this is True it will stop all application of subsequent features. Default is to print the error."},
                  {"name": "dry_run", "default": "False", "required": "False", "type": "boolean", "desc": "Just list the features we would apply, don't actually apply them."},
                  {"name": "show_copy_errors", "default": "False", "required": "False", "type": "boolean", "desc": "Show SettingWitCopyWarnings if you want. Otherwise we suppress"}, 
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": [""]
         }
    """

    if not show_copy_errors:
        pd.options.mode.chained_assignment = None

    # I could maybe multi thread this? Or Multi Process?
    cur_cols = apply_df.columns.tolist()  
    for k, v in feat_dict.items():
        if k not in cur_cols or rerun_apply:
            if debug:
                print(f"Applying {k} - {v['desc']}")
            if not dry_run:
                try:
                    apply_df[k] = apply_df.apply(lambda row: v['func'](row), axis=1)
                except Exception as e:
                    print(f"Exception applying feature {k}")
                    print(f"Exception: {str(e)}")

                    if stop_on_fail:
                        print("Exiting due to stop_on_fail set to True")
                        return apply_df
                    else:
                        apply_df[k] = None
            else:
                apply_df[k] = None
        else:
            if debug:
                print(f"Clause {k} already exists in data set and rerun_apply is False - Not Running")

    if not show_copy_errors:
        pd.options.mode.chained_assignment = 'warn'

    return apply_df

def apply_custom_clauses(apply_df, feat_dict, custom_clauses, rerun_apply=False, stop_on_fail=False, dry_run=False, debug=False, show_copy_errors=False):
    """ {"name": "apply_custom_clauses", 
         "desc": "Take a dataframe of data, and apply features from a feature dictionary, and a list of custom clauses and calculates features based on that. Return the dataframe with the feature columns applied",
         "return": "Dataframe with applied features as columns", 
         "examples": ["mydf = apply_custom_clauses(mydf, myfeatures, myclauses)"], 
         "args": [{"name": "apply_df", "default": "NA", "required": "True", "type": "pd.DataFrame", "desc": "Dataframe of data to apply features to"},
                  {"name": "feat_dict", "default": "NA", "required": "True", "type": "dict", "desc": "Dictionary of features to apply"},
                  {"name": "custom_clauses", "default": "NA", "required": "True", "type": "list", "desc": "List of custom clauses to apply"},
                  {"name": "rerun_apply", "default": "False", "required": "False", "type": "boolean", "desc": "If the column already exists, we don't apply the feature unless this is true"},
                  {"name": "stop_on_fail", "default": "False", "required": "False", "type": "boolean", "desc": "If a feature application has an exception, if this is True it will stop all application of subsequent features. Default is to print the error."},
                  {"name": "dry_run", "default": "False", "required": "False", "type": "boolean", "desc": "Just list the features we would apply, don't actually apply them."},
                  {"name": "show_copy_errors", "default": "False", "required": "False", "type": "boolean", "desc": "Show SettingWitCopyWarnings if you want. Otherwise we suppress"}, 
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": [""]
         }
    """

    if not show_copy_errors:
        pd.options.mode.chained_assignment = None

    cur_cols = apply_df.columns.tolist()
    for i in custom_clauses:
        if i not in cur_cols or rerun_apply:
            if debug:
                print(f"Processing clause: {i}")
            clause_op, feats = parse_custom_clause(i)
            if clause_op.find("Err:") < 0:
                proc_clause = True
                for f in feats:
                    if f not in feat_dict:
                        print(f"Feature {f} in {i} does not exist in features list - Cannot process")
                        proc_clause = False
                        break
                if proc_clause:
                    for f in feats:
                        if f not in apply_df.columns.tolist():
                            print(f"Feature {f} from {i} is in features list, but not in data frame columns. Perhaps you haven't applied features? - Cannot process")
                            proc_clause = False
                            break
                if proc_clause:
                    if not dry_run:
                        try:
                            if clause_op == "_AND_":
                                apply_df[i] = apply_df.apply(lambda r: 1 if all([r[f] for f in feats]) else 0, axis=1)
                            elif clause_op == "_OR_":
                                apply_df[i] = apply_df.apply(lambda r: 1 if any([r[f] for f in feats]) else 0, axis=1)
                            else:
                                print("Oh boy we shouldn't be here")
                        except Exception as e:
                            print(f"Exception applying custom clause {i}")
                            print(f"Exception: {str(e)}")
                            if stop_on_fail:
                                print("Exiting due to stop_on_fail set to True")
                                return apply_df
                            else:
                                apply_df[i] = None
                    else:
                        apply_df[i] = None
                else:
                    print(f"Clause {i} not processed")
        else:
            if debug:
                print(f"Clause {i} already exists in data set and rerun_apply is False - Not Running")

    if not show_copy_errors:
        pd.options.mode.chained_assignment = 'warn'

    return apply_df


def parse_custom_clause(cclause):
    """ {"name": "parse_custom_clause", 
         "desc": "Parse a custom clause into its component parts and return a separated (_AND_ or _OR_) and a list of the component features that make up the clause",
         "return": "Separator and list of features that make up a clause", 
         "examples": ["parsed_clauses = parse_custom_clause(myclauses)"], 
         "args": [{"name": "cclause", "default": "NA", "required": "True", "type": "string", "desc": "Custom clause as a string"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": [""]
         }
    """
    ret_items = []
    ret_sep = "Err:General Error"
    if cclause.find("_OR_") < 0 and cclause.find("_AND_") < 0:
        ret_sep = f"Err:_AND_ or _OR_ Not Found in {cclause} must include _AND_ or _OR_ (note case)"
    elif cclause.find("_OR_") >= 0 and cclause.find("_AND_") >= 0:
        ret_sep = f"Err:_AND_ and _OR_ Both Found in {cclause} Must Select one or the other"
    else:
        ret_sep = "_AND_"
        if cclause.find("_OR_") >= 0:
            ret_sep = "_OR_"
        ret_items = cclause.split(ret_sep)
    return ret_sep, ret_items


def ret_custom_clause_group(cc, this_feat_dict):
    """ {"name": "ret_custom_clause_group", 
         "desc": "Take a custom clause and feature dict and get the group it belongs to. If all clauses are the same group, return that, else return 'Compound Groups'",
         "return": "Group name as a string", 
         "examples": ["clause_group = ret_custom_clause_group(myclause, feat_dict)"], 
         "args": [{"name": "cc", "default": "NA", "required": "True", "type": "string", "desc": "Custom clause as a string"},
                  {"name": "this_feat_dict", "default": "NA", "required": "True", "type": "dict", "desc": "Dictionary of features that include the individual clauses"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": ["Only returns a group if all clauses are in the group, otherwise returns static Compound Groups"]
         }
    """


    ret_grp = "non_calc"
    clause_op, clause_items = parse_custom_clause(cc)
    if clause_op.find("Err") < 0:
        mygroups = []
        for i in clause_items:
            if i in this_feat_dict:
                mygroups.append(this_feat_dict[i]['group'])
        mygroups = list(set(mygroups))
        if len(mygroups) == 1:
            ret_grp = mygroups[0]
        else:
            ret_grp = "Compound Groups"
    return ret_grp

def ret_custom_clause_desc(cc, this_feat_dict):
    """ {"name": "ret_custom_clause_desc", 
         "desc": "Take a custom clause and feature dict and get the description for the clause.",
         "return": "Desciption as a string", 
         "examples": ["clause_group = ret_custom_clause_desc(myclause, feat_dict)"], 
         "args": [{"name": "cc", "default": "NA", "required": "True", "type": "string", "desc": "Custom clause as a string"},
                  {"name": "this_feat_dict", "default": "NA", "required": "True", "type": "dict", "desc": "Dictionary of features that include the individual clauses"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "dependent_functions": "",
         "limitations": [""]
         }
    """

    ret_desc = "Error Getting Description"
    clause_op, clause_items = parse_custom_clause(cc)
    if clause_op.find("Err") < 0:


        ret_desc = "("
        for ai in clause_items:
            if ai not in this_feat_dict:
                ret_desc += f"{ai} desc not found {clause_op.replace('_', '')} "
            else:
                ret_desc += f"{this_feat_dict[ai]['desc']} {clause_op.replace('_', '')} "
        if clause_op == "_AND_":
            ret_desc = ret_desc[0:-5]
        else:
            ret_desc = ret_desc[0:-4]
        ret_desc += ")"
    return ret_desc




def calculate_features(event_df, feat_dict, event_item='cust_account', custom_clauses=[], debug=False):
    """{"name": "calculate_features",
         "desc": "Take an event_df, feature_dict, event_field and optional custom_clauses and calculate the percentages within the popuplation ",
         "return": "A calculated feature dictionary",
         "examples": [["calc_dict = calculate_features(event_df, my_features, event_field='zeropadded_accountnum', custom_clauses=clauses)", "Calculate the calculated dict"]
         ], 
         "args": [{"name": "event_df", "default": "", "required": "True", "type": "pd.DataFrame", "desc": "The Dataframe to calculate"},
                  {"name": "feat_dict", "default": "", "required": "True", "type": "dict", "desc": "Dictionary of features as defined in feature specification"},
                  {"name": "event_item", "default": "cust_account", "required": "False", "type": "string", "desc": "The field to use for percentage calculations"},
                  {"name": "custom_clauses", "default": "[]", "required": "False", "type": "list", "desc": "List of combination clauses to check for"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "limitations": [""]
         }
    """

    all_item_list = list(set(event_df[event_item].tolist()))
    all_cols = event_df.columns.tolist()
    all_item_count = len(all_item_list)
    init_calc_dict = {}
    for k, v in feat_dict.items():
        if v['group'] != 'non_calc':
            if k in all_cols:
                init_calc_dict[k] = list(set(event_df[event_df[k] == 1][event_item].tolist()))
            else:
                init_calc_dict[k] = None
    for c in custom_clauses:
        if c in all_cols:
            init_calc_dict[c] = list(set(event_df[event_df[c] == 1][event_item].tolist()))
        else:
            init_calc_dict[c] = None

    calc_dict = {}
    for k, v in init_calc_dict.items():
        if v is not None:
            calc_dict[k] = {'accts': v, 'cnt_accts': len(v), 'perc_accts': round(len(v) / all_item_count, 2)}
        else:
            calc_dict[k] = {'accts': None, 'cnt_accts': "na", 'perc_accts': "na"}

    return calc_dict



def output_features(feat_dict, custom_clauses=[], event_df=None, calc_features=True, event_item='cust_account',
                    output_type="dataframe", md_output_header=None, display_features=None, display_groups=None, debug=False):
    """{"name": "output_features", 
         "desc": "Take a features dictionary and output in a variety of formats, both as applied to a event dataset, and just a list of features (no calculations)",
         "return": "Output based on the output_type variable",
         "examples": [["feat_md = output_features(my_features, custom_clauses=cluases)", "Output, in markdown (default) format the features defined in the feature dictionary"],
                      ["feat_df = output_features(my_features, customer_clauses=clauses, event_df=filter_df, event_item='zeropadded_accountnum', output_type='dataframe')", "Output as a dataframe with calculated values for the dataframe filter_df"]
         ],
         "args": [{"name": "feat_dict", "default": "", "required": "True", "type": "dict", "desc": "Dictionary of features as defined in feature specification"},
                  {"name": "custom_clauses", "default": "[]", "required": "False", "type": "list", "desc": "List of combination clauses to check for"},
                  {"name": "event_df", "default": "None", "required": "False", "type": "None or pd.DataFrame", "desc": "If None, it will only list the features, if pd.DataFrame, it will calculate an use that"},
                  {"name": "calc_features", "default": "True", "required": "False", "type": "boolean", "desc": "If a dataframe is provided for event_df, this can trigger a print only on the features. If False, it will print features without calc, even if event_df is provided"},
                  {"name": "event_item", "default": "cust_account", "required": "False", "type": "string", "desc": "If event_df is a dataframe and calc_features is true, this value will determine how percentages are calculated for each feature. "},
                  {"name": "output_type", "default": "dataframe", "required": "False", "type": "string", "desc": "How the output is formated, allowed: dataframe (default) or markdown"},
                  {"name": "md_output_header", "default": "None", "required": "False", "type": "string or None", "desc": "Header if using markdown output (otherwise ignored)"},
                  {"name": "display_features", "default": "None", "required": "False", "type": "None or List", "desc": "A list of features to display, otherwise use all"},
                  {"name": "display_groups", "default": "None", "required": "False", "type": "None or List", "desc": "A list of groups to display, otherwise use all"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Enable debug messages"}
                  ],
         "integration": "",
         "instance": "",
         "access_instructions": "",
         "limitations": [""]
         }
    """


    
    display_features_only = False
    if event_df is None or calc_features == False:
        display_features_only = True
    if display_features is None:
        display_features = list(feat_dict.keys())
        display_features += custom_clauses
    if not display_features_only and event_item not in event_df.columns.tolist() :
        print(f"Warning {event_item} not a column in event_df - Cannot Display")
        return f"### Error on Formatting\n"

    if display_features_only:
        calc_features = {}
        total_items = -1
    else:
        print("Calculating Features")
        calc_features = calculate_features(event_df, feat_dict, event_item=event_item, custom_clauses=custom_clauses, debug=debug)
        print("Feature Calculation Complete")
        total_items = len(list(set(event_df[event_item].tolist())))


    out_groups = {}

    # Calculate groups (including the non_calc)
    for f in display_features:
        this_group = ""
        this_desc = ""
        this_val = ""
        if f in feat_dict:
            this_group = feat_dict[f]['group']
            this_desc = feat_dict[f]['desc']
        elif f in custom_clauses:
            this_group = ret_custom_clause_group(f, feat_dict)
            this_desc = ret_custom_clause_desc(f, feat_dict)
        else:
            this_group = "not_found"
            this_desc = "Feature not found"

        if this_group not in out_groups:
            out_groups[this_group] = []
        cnt_val = None
        per_val = None
        if f in calc_features:
            cnt_val = None
            per_val = None
            if isinstance(calc_features[f]['cnt_accts'], str):
               cnt_val = calc_features[f]['cnt_accts']
            else:
               cnt_val = f"{calc_features[f]['cnt_accts']:,}"
            if isinstance(calc_features[f]['perc_accts'], str):
                per_val = calc_features[f]['perc_accts']
            else:
                per_val = f"{calc_features[f]['perc_accts'] * 100:.2f}%"
            this_val = {"cnt_val": cnt_val, "per_val": per_val, "feature": f, "desc": this_desc}
        else:
            this_val = {"cnt_val": "NA", "per_val": "NA", "feature": f, "desc": this_desc}
        out_groups[this_group].append(this_val)

    if display_groups is None:
        display_groups = sorted(list(out_groups.keys()))

    if display_features_only:
        if output_type == "markdown":
            if md_output_header is None:
                md_output_header = "# All Feature List\n"
                md_output_header += "-------------------\n"
                md_output_header += f"List of all feaures in provided feature dictionary with no DF calculations\n"
                md_output_header += "\n"
            retval = md_output_header
            grp_header = "\n"
            grp_header += "## ~~grp~~\n"
            grp_header += "-----------------------\n"
            grp_header += "| Feature | Description |\n"
            grp_header += "| ------- | ----------- |\n"

            for grp in display_groups:
                this_header = grp_header.replace("~~grp~~", grp)
                retval += this_header
                for i in out_groups[grp]:
                    retval += f"| {i['feature']} | {i['desc']} |\n"
                retval += "\n"
        elif output_type == "dataframe":
            df_list = []
            for grp in display_groups:
                for i in out_groups[grp]:
                    df_list.append({"display_group": grp, "feature": i['feature'], "description": i['desc']})
            retval = pd.DataFrame(df_list)
        else:
            print(f"output_type: {output_type} not supported - try dataframe or markdown")
            retval = ""
    else:
        if output_type == "markdown":
            if md_output_header is None:
                md_output_header = "# Basic Feature Breakdown\n"
                md_output_header += "------------------------\n"
                md_output_header += f"Breakdown of features for {total_items:,} items\n"
                md_output_header += "\n"
            retval = md_output_header
            grp_header = "\n"
            grp_header += "## ~~grp~~\n"
            grp_header += "-----------------------\n"
            grp_header += "| Count | Perc | Feature | Description |\n"
            grp_header += "| ----- | ---- | ------- | ----------- |\n"

            for grp in display_groups:
                if grp == 'non_calc':
                    continue
                this_header = grp_header.replace("~~grp~~", grp)
                retval += this_header
                for i in out_groups[grp]:
                    retval += f"| {i['cnt_val']} | {i['per_val']} | {i['feature']} | {i['desc']} |\n"
                retval += "\n"
        elif output_type == 'dataframe':
            df_list = []
            for grp in display_groups:
                if grp != "non_calc":
                    for i in out_groups[grp]:
                        try:
                            i_cnt = int(i['cnt_val'].replace(",", ""))
                        except:
                            i_cnt = np.nan
                        try:
                            f_per = float(i['per_val'].replace("%", ""))
                        except:
                            f_per = np.nan
                        df_list.append({"display_group": grp, "feature": i['feature'], "feature_count": i_cnt,
                                        "all_items": total_items, "feature_percentage": f_per, "description": i['desc']})
            retval = pd.DataFrame(df_list)
        else:
            print(f"output_type: {output_type} not supported - try dataframe or markdown")
            retval = ""

    return retval


#########################################################
##### get_doc function
# This function must be in every file
# It does not need to be, nor should it be edited
# This function is needed in order get the doc items from globals

#def get_doc(func_name, doc_item):
#    try:
#        retval = get_func_doc_item(func_name, doc_item, globals())
#    except:
#        retval = "error"
#    return retval

########################################################
# And finally, when this file is loaded, call the basic help to let the user know it was loaded
# Call Basic help on first load so users know it's been loaded

#feature_calc_help("basic")
