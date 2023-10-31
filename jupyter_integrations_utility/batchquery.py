# Doc Functions
from IPython.display import display, Markdown
import datetime
import time
import json
import sys
import os
import operator
from inspect import isfunction
import pandas as pd
from jupyter_integrations_utility.funcdoc import *


load_name = "batch_query"
if load_name not in loaded_helpers:
    loaded_helpers.append(load_name)


def batch_query_help(func_name=None, debug=False):
    if debug:
        print("Running with debug")

    title = "Batch Query Helpers"
    help_func = "batch_query_help"
    exp_func = "batch_list_in"

    doc_functions = {
    "general utility": [
        "write_xlsx",
        "batch_list_in",
        "batch_by_date",
        "df_expand_col",
        "make_list_like_any"
    ],
    "date handling": [
        "get_splunk_date",
        "resolve_start_date",
        "handle_dates",
        "range_dates",
        "range_hist"
    ]
    }


    main_help(title, help_func, doc_functions, globals(), exp_func=exp_func, func_name=func_name, debug=debug)




######################################################################################################################################################
###################################################################
# general utility
# Documentation: Complete
#

def write_xlsx(outputfile, dfsheets):
    """ {"name": "write_xlsx",
         "desc": "Write an xlsx file with one or more dataframes on defined worksheets",
         "return": "None - But does output an excel file",
         "examples": [
            ["write_xlsx('my_excel_file_name.xlsx', {'Worksheet1': df1, 'Worksheet2': df2})", "Writes an excel file named my_excel_file_name.xlsx with two worksheets named Worksheet1 and Worksheet2"]
         ],
         "args": [{"name": "outputfile", "default": "NA", "required": "True", "type": "string", "desc": "Name of spreadsheet to output (full name)"},
                  {"name": "dfsheets", "default": "NA", "required": "True", "type": "boolean", "desc": "Dictionary with keys being worksheet names and values being dataframes to write."}
                  ],
         "integration": "Any",
         "instance": "Any",
         "access_instructions": "na",
         "limitations": ["Requires xlsxwriter"]
         }
    """
    try:
        import xlsxwriter
    except:
        print(f"xlsxwriter did not properly import - No XLSX outputted")
        return None

    wbwriter = pd.ExcelWriter(outputfile, engine='xlsxwriter', datetime_format='yyyy-mm-dd hh:mm:ss')
    mywb = wbwriter.book
    for mysheet in dfsheets.keys():
        mydf = dfsheets[mysheet]
        mydf.to_excel(wbwriter, sheet_name=mysheet, startrow=1, header=False, index=False)

        myws = wbwriter.sheets[mysheet]
        col_settings = [{'header': column} for column in mydf.columns]
        (max_row, max_col) = mydf.shape
        myws.add_table(0, 0, max_row, max_col - 1, {'columns': col_settings})
        len_list = [min(max([len(str(r)) for r in mydf[col].tolist() + [col + "   "]]), 100) for col in mydf.columns]
        for i, w, in enumerate(len_list):
            myws.set_column(i, i, w)
        myws.freeze_panes(1, 0)

    mywb.close()
    print(f"XLSX Output to {outputfile} complete")



def batch_list_in(batchlist, base_query, integration, instance, tmp_dict={}, batchsize=500, list_quotes='single', list_sep=', ', dedupe=True, remove_none=True, debug=False):
    """ {"name": "batch_list_in",
         "desc": "Take in a query, list, integration, and instance and split the list up into batched, returning all results as one dataframe",
         "return": "A dataframe with the result of all batches combined",
         "examples": ["combined_df = batch_list_in(ip_list, ip_query, 'impala', 'prod')"],
         "args": [{"name": "batchlist", "default": "None", "required": "True", "type": "list", "desc": "List of items to be batched and queried"},
                  {"name": "base_query", "default": "None", "required": "True", "type": "string", "desc": "Query that is complete except for the string ~~here~~ which will be replaced with the current batch"},
                  {"name": "integration", "default": "None", "required": "True", "type": "string", "desc": "The integration the query will be submitted to (i.e. splunk, tera, impala)"},
                  {"name": "instance", "default": "None", "required": "True", "type": "string", "desc": "The instance of the previously provided integration that will be used (i.e. prod, dev)"},
                  {"name": "tmp_dict", "default": "{}", "required": "False", "type": "dict", "desc": "Instructions for temp table, pass the table name to use temp, and pull_final_results if you want all results back"},
                  {"name": "batchsize", "default": "500", "required": "False", "type": "integer", "desc": "The max number of items in a batch."},
                  {"name": "list_quotes", "default": "single", "required": "False", "type": "string", "desc": "Whether to use single or double quotes, or blank  on list items. Single is default best for SQLish, double may work better for Splunk types"},
                  {"name": "list_sep", "default": ", ", "required": "False", "type": "string", "desc": "How the list gets seperated. ', ' is the default and works for SQL IN clauses. Consider ' OR ' for SPLUNK index queries"},
                  {"name": "dedupe", "default": "True", "required": "False", "type": "boolean", "desc": "Deduplicate the list, prior to submitting"},
                  {"name": "remove_none", "default": "True", "required": "False", "type": "boolean", "desc": "Remove null values from the list. "},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Turns on debug messages"}
                  ],
         "integration": "Any",
         "instance": "Any",
         "access_instructions": "na",
         "limitations": ["Only works on list item batches"]
         }
    """

    vol_dict = {
                    "table_name": None,
                    "pre_create": "CREATE MULTISET VOLATILE TABLE ~~tname~~ AS(\n",
                    "post_create": ") WITH DATA ON COMMIT PRESERVE ROWS",
                    "pre_insert": "INSERT INTO ~~tname~~\n",
                    "post_insert": "",
                    "created": False,
                    "pull_final_results": False
               }


    if tmp_dict is not None:
        vol_dict.update(tmp_dict)

    bTemp = False
    ret_results = vol_dict['pull_final_results']
    if vol_dict['table_name'] is not None:
        bTemp = True

    results_var = f"prev_{integration}_{instance}"
    ipy = get_ipython()

    if debug:
        print("Running query using %s instance %s" % (integration, instance))

    if base_query.find("~~here~~") < 0:
        print("Warning: We typically Need to know where to put in the batched list, your query should  have '~~here~~' in it")
        print("Example:  field in (~~here~~) --if you are doing a list of said field")
        print("This is not a required, just a warning")

    if integration in ipy.user_ns['jupyter_loaded_integrations'].keys():
        integration_var = ipy.user_ns['jupyter_loaded_integrations'][integration]
    else:
        print("Integration: %s not loaded" % integration)
        return pd.DataFrame()

    if not ipy.user_ns[integration_var].instances[instance]['connected']:
        print("%s integration instance %s is not connected, please connect" % (integration, instance))
        return pd.DataFrame()

    if dedupe:
        batchlist = list(set(batchlist))

    if remove_none:
        batchlist = [x for x in batchlist if x is not None and pd.isna(x) == False]

    list_cnt = len(batchlist)
    if bTemp:
        print(f"Temp Table Batching - Table Name: {vol_dict['table_name']}")

    print("Total Items in Batchlist: %s" % list_cnt)

    curs = 0
    next_run = True
    out_df = pd.DataFrame()
    loops = 0


    full_s_time = int(time.time())
    print(f"Starting Batch List In")
    while next_run:
        loops += 1
        stidx = curs
        enidx = curs + batchsize
        if enidx > list_cnt:
            next_run = False
        thisbatch = batchlist[stidx:enidx]
        curs = enidx
        this_len = len(thisbatch)
        if list_quotes == 'single' and list_sep == ", ":
            this_str = str(thisbatch)[1:-1]  # just due the default list separator
        elif list_quotes == "single":
            this_str = f"'{list_sep}'".join(thisbatch)
            this_str = f"'{this_str}'"
        elif list_quotes == "double":
            this_str = f'"{list_sep}"'.join(thisbatch)
            this_str = f'"{this_str}"'
        elif list_quotes == "blank":
            this_str = f"{list_sep}".join(thisbatch)
        else:
            print("\t Error must use single or double as your list_quotes")

        print(f"\t Batch: {loops} - {this_len} Items - {stidx} to {enidx}")
        this_query = base_query.replace("~~here~~", this_str)
        try:
            del ipy.user_ns[results_var]
        except:
            pass
        if debug:
            print("")
            print("Cur Query")
            print(this_query)
        t_s_time = int(time.time())
        if this_len > 0:
            if bTemp:
                if not vol_dict['created']:
                    pre_q = vol_dict['pre_create'].replace('~~tname~~', vol_dict['table_name'])
                    post_q = vol_dict['post_create']
                else:
                    pre_q = vol_dict['pre_insert'].replace('~~tname~~', vol_dict['table_name'])
                    post_q = vol_dict['post_insert']
                this_query = f"{pre_q}{this_query}{post_q}"
            ipy.run_cell_magic(integration, instance + " -d", this_query)
            if vol_dict['created'] == False:
                vol_dict['created'] = True
        else:
            print("Batch is a final batch and you connected perfectly with batch size - skipping due to no more items!")
        t_q_time = int(time.time())
        try:
            if not bTemp:
                these_df = ipy.user_ns[results_var]
            else:
                these_df = pd.DataFrame()
        except:
            these_df = pd.DataFrame()
            if this_len > 0:
                print("Error on batch")
        out_df = pd.concat([out_df, these_df], ignore_index=True)
        t_f_time = int(time.time())

        t_t_time = t_f_time - t_s_time
        t_qt_time = t_q_time - t_s_time
        t_c_time = t_f_time - t_q_time

        print(f"\t\t {len(these_df)} results in list batch {loops} - total: {len(out_df)}")
        print(f"\t\t {t_t_time:,} seconds in batch (Query: {t_qt_time:,} seconds - DF Concat: {t_c_time:,} seconds)")
        these_df = None

    full_e_time = int(time.time())
    full_t_time = full_e_time - full_s_time
    a_time = full_t_time / loops
    print(f"Total time: {full_t_time:,} seconds (Average of {a_time:.2f} seconds over {loops} loops)")

    if bTemp:
        test_query = f"select count(1) as tcnt from {vol_dict['table_name']}"
        ipy.run_cell_magic(integration, instance + " -d", test_query)
        cnt_df = ipy.user_ns[results_var]
        res_cnt = cnt_df['tcnt'].tolist()[0]
        if ret_results:
            # In this case, we need pull the full table results. 
            print(f"Note: Total results for this table is {res_cnt} - Pulling results large results will take some time")
            pull_query = f"select * from {vol_dict['table_name']}"
            ipy.run_cell_magic(integration, instance + " -d", pull_query)
            out_df = ipy.user_ns[results_var]
        else:
            print(f"Temp Table Loaded with {res_cnt} rows in table: {vol_dict['table_name']}")

    return out_df


def batch_by_date(base_query, integration, instance, list_items, date_batch_type, date_start, date_end, range_batchdays=30, range_splunk=False, range_datefield="asofdate", range_add_ts=False, hist_str="_hs_", hist_format="%Y%m", hist_current_str= "_ct", hist_date_clauses=[], tmp_dict={}, batchsize=500, print_only=False, debug=False):
    """ {"name": "batch_by_date",
         "desc": "Take a query and date range and break it up in date chunks for handling long combined queries. Also uses the batch list function to lots of items.",
         "return": "Dataframe of combined results",
         "examples": [],
         "args": [{"name": "base_query", "default": "None", "required": "True", "type": "string", "desc": "The base query. It should have a ~~here~~ for list items and a ~~date~~ for the dates"},
                  {"name": "integration", "default": "None", "required": "True", "type": "string", "desc": "The integration to submit the query too"},
                  {"name": "instance", "default": "None", "required": "True", "type": "string", "desc": "The instance of the integration"},
                  {"name": "list_items", "default": "None", "required": "True", "type": "list", "desc": "A list of items to pass in to the batch function. Replace ~~here~~ in batches"},
                  {"name": "date_batch_type", "default": "None", "required": "True", "type": "string", "desc": "Should be 'hist' (for history tables) or 'range' (for partitioned tables)"},
                  {"name": "date_start", "default": "None", "required": "False", "type": "string or None", "desc": "Start date of the query, if not passed we use 90 days prior today"},
                  {"name": "date_end", "default": "now", "required": "False", "type": "string", "desc": "End date of the query (or now for today)"},
                  {"name": "range_batchdays", "default": "30", "required": "False", "type": "integer", "desc": "Number of days to batch if using range"},
                  {"name": "range_splunk", "default": "False", "required": "False", "type": "boolean", "desc": "Use Splunk earliest and latest, and splunk format instead of date field"},
                  {"name": "range_datefield", "default": "asofdate", "required": "False", "type": "string", "desc": "Name of datefield to replace in where clause"},
                  {"name": "range_add_ts", "default": "False", "required": "False", "type": "boolean", "desc": "Add ' 00:00:00' to dates for Teradata timestamps"},
                  {"name": "hist_str", "default": "_hs_", "required": "False", "type": "string", "desc": "Static string on history tables if using hist"},
                  {"name": "hist_format", "default": "%Y%m", "required": "False", "type": "string", "desc": "Date format for hist tables (%Y%m and %y%m supported)"},
                  {"name": "hist_current_str", "default": "_ct", "required": "False", "type": "string", "desc": "String for the current table if using hist"},
                  {"name": "hist_date_clauses", "default": "[]", "required": "False", "type": "list", "desc": "A list of 4 item lists that can be used to replace parts of the query based on the hist date - Careful"},
                  {"name": "tmp_dict", "default": "{}", "required": "False", "type": "dict", "desc": "Instructions for temp table, pass the table name to use temp, and pull_final_results if you want all results back"},
                  {"name": "batchsize", "default": "500", "required": "False", "type": "integer", "desc": "Number of items in list to batch (this is done per date)"},
                  {"name": "print_only", "default": "False", "required": "False", "type": "boolean", "desc": "Only print one iteration of the query"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Print debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": []
         }
    """


    vol_dict = {
                    "table_name": None,
                    "pre_create": "CREATE MULTISET VOLATILE TABLE ~~tname~~ AS(\n",
                    "post_create": ") WITH DATA ON COMMIT PRESERVE ROWS",
                    "pre_insert": "INSERT INTO ~~tname~~\n",
                    "post_insert": "",
                    "created": False,
                    "pull_final_results": False
               }

    ipy = get_ipython()
    results_var = f"prev_{integration}_{instance}"

    if tmp_dict is not None:
        vol_dict.update(tmp_dict)

    bTemp = False
    ret_results = vol_dict['pull_final_results']

    if vol_dict['table_name'] is not None:
        bTemp = True

    # We set this back to False no matter one. We know via ret_results if this was the inital call and they want results. 
    vol_dict['pull_final_results'] = False


    date_start = resolve_start_date(date_start)
    cur_dt = datetime.datetime.now()
    cur_dt_str = cur_dt.strftime('%Y-%m-%d')
    cur_dt_mon_str = cur_dt.strftime('%Y-%m')

    op_list = ['gt', 'lt', 'ge', 'le', 'eq', 'neq']
    out_df = None

    if date_batch_type == "range":
        date_list = range_dates(date_start, batchsize=range_batchdays, end_date=date_end, debug=debug)
    elif date_batch_type == "hist":
        date_list = range_hist(date_start, hist_str=hist_str, hist_format=hist_format, current_str=hist_current_str, end_date=date_end, debug=debug)
    else:
        print(f"Only range and hist supported, you provided: {date_batch_type}")
        return out_df

    out_df = pd.DataFrame()

    if len(list_items) == 0:
        print_only = True
    if print_only:
        print("Printing one iteration of the date loop")
        print("")

    loops = 0
    for dl in date_list:
        loops += 1
        if loops > 1 and print_only == True:
            break
        if date_batch_type == "hist":
            print(f"*** Date Loop {loops} running for Dates {dl}")
            this_query = base_query.replace("~~date~~", dl)
            if len(hist_date_clauses) > 0:
                for myclause in hist_date_clauses:
                # ["~~aid~~", "_hs_202103", "ge", "pos.aiid AS aiid,", "'not_tracked' AS aiid,"]
                    repl_val = myclause[0]
                    check_val = myclause[1]
                    check_operator = myclause[2]
                    op_list = ['gt', 'lt', 'ge', 'le', 'eq', 'ne']
                    if check_operator not in op_list:
                        print(f"Provided operator ({check_operator}) not in allowed operators: ({op_list}) - defaulting to equality (eq)")
                        check_operator = "eq"
                    true_val = myclause[3]
                    false_val = myclause[4]
                    temp_op = operator.methodcaller(check_operator, dl, check_val)
                    if temp_op(operator):
                        replacement_val = true_val
                    else:
                        replacement_val = false_val
                    temp_op = None
                    this_query = this_query.replace(repl_val, replacement_val)
            if debug:
                print(f"Value after date dependent clauses: {this_query}")

        elif date_batch_type == "range":
            t_d_start = dl[0]
            t_d_end = dl[1]

            if range_splunk:
                t_d_start = get_splunk_date(t_d_start)
                t_d_end = get_splunk_date(t_d_end)

            if range_add_ts or range_splunk:
                if range_splunk:
                    mysep = ":"
                else:
                    mysep = " "
                t_d_start = f"{t_d_start}{mysep}00:00:00"
                t_d_end = f"{t_d_end}{mysep}00:00:00"

            print(f"Loop {loops} running for Dates {t_d_start} to {t_d_end}")
            if not range_splunk:
                date_where = f"{range_datefield} >= '{t_d_start}' and {range_datefield} < '{t_d_end}'"
            else:
                date_where = f'earliest="{t_d_start}" AND latest="{t_d_end}"'
            this_query = base_query.replace("~~date~~", date_where)
        if print_only:
            print_query(this_query, integration, instance)
        else:
            cur_df = pd.DataFrame()
            cur_df = batch_list_in(list_items, this_query, integration, instance, tmp_dict=vol_dict, batchsize=batchsize, debug=debug)
            if bTemp == False:
                if len(cur_df) > 0:
                    out_df = pd.concat([out_df, cur_df], ignore_index=True)
                    print(f"\t {len(cur_df)} results in date batch {loops} - total: {len(out_df)}")
                else:
                    print(f"\t No results on {loops} date batch")
            else:
                if vol_dict['created'] == False:
                    vol_dict['created'] = True

    if bTemp:
        test_query = f"select count(1) as tcnt from {vol_dict['table_name']}"
        ipy.run_cell_magic(integration, instance + " -d", test_query)
        cnt_df = ipy.user_ns[results_var]
        res_cnt = cnt_df['tcnt'].tolist()[0]
        if ret_results:
            # In this case, we need pull the full table results. 
            print(f"Note: Total results for this table is {res_cnt} - Pulling results large results will take some time")
            pull_query = f"select * from {vol_dict['table_name']}"
            ipy.run_cell_magic(integration, instance + " -d", pull_query)
            out_df = ipy.user_ns[results_var]
        else:
            print(f"Temp Table Loaded with {res_cnt} rows in table: {vol_dict['table_name']}")

    return out_df

def get_splunk_date(strdate):
    """ {"name": "get_splunk_date",
         "desc": "Takes a date in YYYY-MM-DD format and outputs in splunk M/D/YYYY format",
         "return": "A string of the converted date",
         "examples": [["mysplunkdate = get_splunk_date('2023-05-01')", "Convert 2023-05-01 to 5/1/2023"]],
         "args": [{"name": "strdate", "default": "None", "required": "True", "type": "string", "desc": "Date in YYYY-MM-DD format"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "na",
         "limitations": []
         }
    """
    mydt = datetime.datetime.strptime(strdate, "%Y-%m-%d")
    myday = str(int(datetime.datetime.strftime(mydt, "%d")))
    mymon = str(int(datetime.datetime.strftime(mydt, "%m")))
    myyear = datetime.datetime.strftime(mydt, "%Y")
    myretdate = f"{mymon}/{myday}/{myyear}"
    return myretdate

def df_expand_col(newdf, srccol, make_json=False, remove_srccol=False):
    """ {"name": "df_expand_col",
         "desc": "Takes a column name that should be a dictionary and expands that column into columns for each dict item",
         "return": "A list of the tables extenstions needed provided the list of dates",
         "examples": ["mydf = df_expand_col(mydf, 'my_dict_col')"],
         "args": [{"name": "newdf", "default": "None", "required": "True", "type": "pd.DataFrame", "desc": "The Dataframe with a column that has a dictionary in it"},
                  {"name": "srccol", "default": "None", "required": "True", "type": "string", "desc": "The name of the column with the dictionary in it"},
                  {"name": "make_json", "default": "False", "required": "False", "type": "boolean", "desc": "Try a json.loads on the column prior to parsing the column"},
                  {"name": "remove_srccol", "default": "False", "required": "False", "type": "boolean", "desc": "Remove the srccol (and the 'parsed' col if make_json==True) from the returned Dataframe"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "na",
         "limitations": ["Tries and just makes a note if it fails"]
         }
    """
    orig_src = srccol
    if make_json:
        try:
            newdf['parsed'] = newdf.apply(lambda row: json.loads(row[srccol]) if row[srccol] is not None else None, axis=1)
            srccol = 'parsed'
        except:
            pass
    try: # Try to load as a string representation of a dict (i.e. JSON)
        newdf['col_levels'] = newdf.apply(lambda row: list(json.loads(row[srccol]).keys()) if row[srccol] is not None and row[srccol] == row[srccol] and not isinstance(row[srccol], str) else list(json.loads("{}").keys()), axis=1)
    except TypeError: # If it's a type error, it may just be a a real dict try that...
        newdf['col_levels'] = newdf.apply(lambda row: list(row[srccol].keys()) if row[srccol] is not None and row[srccol] == row[srccol] and not isinstance(row[srccol], str) else [], axis=1)

    col_items = list({x for l in newdf['col_levels'].tolist() for x in l})
    for col in col_items:
        try:
            newdf[srccol + "." + col] = newdf.apply(lambda row: json.loads(row[srccol]).get(col, "") if row[srccol] is not None and row[srccol] == row[srccol] and not isinstance(row[srccol], str) else None, axis=1)
        except TypeError:
            newdf[srccol + "." + col] = newdf.apply(lambda row: row[srccol].get(col, "") if row[srccol] is not None and row[srccol] == row[srccol] and not isinstance(row[srccol], str) else None, axis=1)
    newdf.drop(columns=['col_levels'], inplace=True)

    if remove_srccol:
        if not make_json:
            newdf.drop(columns=[srccol], inplace=True)
        else:
            newdf.drop(columns=['parsed'], inplace=True)
            newdf.drop(columns=[orig_src], inplace=True)
            try:
                newdf.drop(columns=[orig_src], inplace=True)
            except:
                pass
    return newdf


def make_list_like_any(inlist, preany=True, postany=True):
    """ {"name": "make_list_like_any", 
         "desc": "Take any list of items and add % before, after, or both(default) to the item for use in a like any or like all query",
         "return": "The list provided, but with the % added in the appropriate places",
         "examples": [],
         "args": [{"name": "inlist", "default": "None", "required": "True", "type": "list", "desc": "The list of items to add the % to"},
                  {"name": "preany", "default": "True", "required": "False", "type": "boolean", "desc": "Add a % as a prefix on all list items"},
                  {"name": "postany", "default": "True", "required": "False", "type": "boolean", "desc": "Add a % as a suffix on all list items"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "Not specific to a data set, but Like any is specific to only some datasources like teradata",
         "limitations": ["Doesn't check if your query will work, just adds the % to the list items"]
         }
    """
    outlist = inlist
    if preany:
        outlist = ['%' + x for x in outlist if x is not None]
    if postany:
        outlist = [x + '%' for x in outlist if x is not None]

    return outlist



#####################################################################################################################################################
###################################################################
# date handling
# Documentation: Complete
#

def resolve_start_date(s_date):
    """ {"name": "resolve_start_date", 
         "desc": "Checks the provided date, if it's None, then provide a message and provide the date 90 days prior to the current date",
         "return": "A string representation of the current date minus 90 days in YYYY-MM-DD format", 
         "examples": ["date_minus_90 = resolve_start_date(None)"], 
         "args": [{"name": "s_date", "default": "None", "required": "True", "type": "String or None", "desc": "Either a date or None. If None, get 90 days prior to today"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "na",
         "limitations": ["Does not validate the date (if not None) as a proper date"]
         }
    """
    ret_date = ""
    if s_date is not None:
        ret_date = s_date
    else:
        x_days = 90
        str_x_date = (datetime.datetime.now() - datetime.timedelta(days=x_days)).strftime("%Y-%m-%d")
        print("We require a start date, using '%s' (90 days ago) or, you can specify your own with date_start='2020-01-01' (for example)" % str_x_date)
        ret_date = str_x_date
    return ret_date

def handle_dates(base_query, date_col, date_start, date_end, include_and=False):
    """ {"name": "handle_dates", 
         "desc": "Takes in a query, and replaces the string `~~dates~~` with a date start and a date end",
         "return": "Query will dates handled", 
         "examples": ["dated_query = handle_date(myquery, 'asofdate', '2022-01-01', '2022-05-01')"], 
         "args": [{"name": "base_query", "default": "None", "required": "True", "type": "string", "desc": "Query that contains the string `~~dates~~` to be replaced"},
                  {"name": "date_col", "default": "None", "required": "True", "type": "string", "desc": "Name of the column that is used for date ranges (i.e. asofdate)"},
                  {"name": "date_start", "default": "None", "required": "True", "type": "string", "desc": "YYYY-MM-DD representation of the start date"},
                  {"name": "date_end", "default": "None", "required": "True", "type": "string", "desc": "YYYY-MM-DD representation of the end date"},
                  {"name": "include_and", "default": "False", "required": "False", "type": "boolean", "desc": "Include an ' and ' at the beginning of the dates"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "na",
         "limitations": ["Does not validate the start_date and end_date as valid", "Will not check for ~~dates~~ if it doesn't exist, will return the query as provided"]
         }
    """
    dstart = False
    if include_and:
        mydates = " and "
    else:
        mydates = ""
    if date_start is not None:
        mydates += "%s >= '%s'" % (date_col, date_start)
        dstart = True

    if date_end is not None and date_end != "now":
        if dstart:
            mydates += " and "
        mydates += "%s < '%s'" % (date_col, date_end)
    base_query = base_query.replace("~~dates~~", mydates)
    return base_query

def range_dates(start_date, batchsize=30, end_date="now", debug=False):
    """ {"name": "range_dates",
         "desc": "Takes a range of dates and create batches in batchsize days",
         "return": "An list of lists containing a start date and end date for each batch",
         "examples": ["range_list = range_dates('2022-01-01', batchsize=30, end_date='2022-04-01')"],
         "args": [{"name": "start_date", "default": "None", "required": "True", "type": "string", "desc": "The Start date for the batches"},
                  {"name": "batchsize", "default": "30", "required": "False", "type": "integer", "desc": "The number of days in each batch"},
                  {"name": "end_date", "default": "now", "required": "False", "type": "string", "desc": "The end date for the batches, now being todays date"},
                  {"name": "debug", "default": "False", "required": "Fakse", "type": "boolean", "desc": "Turn on debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "na",
         "limitations": ["Does not validate the dates"]
         }
    """
    batches = []
    start_date_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')

    if end_date == 'now':
        end_date_dt = datetime.datetime.now()
        end_date = end_date_dt.strftime('%Y-%m-%d')
        print("End Date note provided - Assuming today: %s" % end_date)
    else:
        end_date_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    end_date_plus_one_dt = end_date_dt + datetime.timedelta(days=1)
    end_date_plus_one = end_date_plus_one_dt.strftime('%Y-%m-%d')
    if debug:
        print("Days in batch: %s" % batchsize)
        print("start_date: %s" % start_date)
        print("End Date: %s" % end_date)
        print("End Date + 1: %s" % end_date_plus_one)

    cur_start_dt = end_date_dt - datetime.timedelta(days=batchsize-1)
    cur_start = cur_start_dt.strftime('%Y-%m-%d')
    cur_end_dt = end_date_plus_one_dt
    cur_end = end_date_plus_one
    if cur_start <= start_date:
        batches.append([start_date, cur_end])
    else:
        batches.append([cur_start, cur_end])

    while cur_start > start_date:
        cur_end_dt = cur_start_dt
        cur_start_dt = cur_start_dt - datetime.timedelta(days=batchsize)
        cur_start = cur_start_dt.strftime('%Y-%m-%d')
        cur_end = cur_end_dt.strftime('%Y-%m-%d')
        if cur_start <= start_date:
            batches.append([start_date, cur_end])
        else:
            batches.append([cur_start, cur_end])
    return batches

def range_hist(start_date, hist_str="_hs_", current_str="_ct", hist_format='%Y%m',end_date="now", debug=False):
    """ {"name": "range_hist",
         "desc": "Provides a list of table extensions for dealing with history tables",
         "return": "A list of the tables extenstions needed provided the list of dates",
         "examples": [],
         "args": [{"name": "start_date", "default": "None", "required": "True", "type": "string", "desc": "The Start date to batch history tables over"},
                  {"name": "hist_str", "default": "_hs_", "required": "False", "type": "string", "desc": "any static string used in historic tables"},
                  {"name": "current_str", "default": "_ct", "required": "False", "type": "string", "desc": "The string appended to the current table"},
                  {"name": "hist_format", "default": "%Y%m", "required": "False", "type": "string", "desc": "The format of the history table, current support %Y%m YYYYMM or %y%m YYMM"},
                  {"name": "end_date", "default": "now", "required": "False", "type": "string", "desc": "The date to end batching (defaults to today)"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Turn on debug messages"}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "na",
         "limitations": ["Does not validate dates", "Only supports two history formats"]
         }
    """
    cur_dt = datetime.datetime.now()
    cur_dt_str = cur_dt.strftime('%Y-%m-%d')
    cur_dt_mon_str = cur_dt.strftime(hist_format)
    supported_formats = ['%Y%m', '%y%m']
    if hist_format not in supported_formats:
        print("Provided hist_format: %s not supported. We support: %s" % (hist_format, supported_formats))
        return []
    batches = []
    start_date_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    start_date_mon = start_date_dt.strftime(hist_format)



    if end_date == 'now':
        end_date_dt = datetime.datetime.now()
        end_date = end_date_dt.strftime('%Y-%m-%d')
        print("End Date note provided - Assuming today: %s" % end_date)
    else:
        end_date_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date_dt.strftime('%Y-%m-%d')

    ind_date_dt = end_date_dt
    ind_date_mon = ind_date_dt.strftime(hist_format)
    while ind_date_mon >= start_date_mon:
        if ind_date_mon == cur_dt_mon_str:
            thisres = current_str
            batches.append(thisres)
        else:
            thisres = ind_date_mon
            batches.append(hist_str + thisres)
        if hist_format == '%Y%m':
            ind_y = int(ind_date_mon[0:4])
            ind_m = int(ind_date_mon[4:])
            ind_m = ind_m - 1
            if ind_m == 0:
                ind_m = 12
                ind_y = ind_y - 1
            ind_date_mon = str(ind_y) + str(ind_m).rjust(2,'0')
        elif hist_format == '%y%m':
            ind_y = int(ind_date_mon[0:2])
            ind_m = int(ind_date_mon[2:])
            ind_m = ind_m - 1
            if ind_m == 0:
                ind_m = 12
                ind_y = ind_y - 1
            ind_date_mon = str(ind_y) + str(ind_m).rjust(2,'0')
        #ind_date_dt = ind_date_dt - datetime.timedelta(days=30)
        #ind_date_mon = ind_date_dt.strftime('%Y%m')
#    FROM cods.auth_pos_ct			pos		-- uses auth_pos_ct for current or _hs_yyyymm for historical
#--FROM cods.auth_pos_hs_202204			pos		-- uses auth_pos_ct for current or _hs_yyyymm for historical
    return batches




