# Doc Functions
from IPython.display import display, Markdown
import datetime
import json
import sys
import os
import operator
from inspect import isfunction
import pandas as pd
loaded_helpers = []

sample_doc = """ {"name": "",
         "desc": "",
         "return": "",
         "examples": [],
         "args": [{"name": "", "default": "", "required": "", "type": "", "desc": ""},
                  {"name": "", "default": "", "required": "", "type": "", "desc": ""},
                  {"name": "", "default": "", "required": "", "type": "", "desc": ""},
                  {"name": "", "default": "", "required": "", "type": "", "desc": ""},
                  {"name": "", "default": "", "required": "", "type": "", "desc": ""},
                  {"name": "", "default": "", "required": "", "type": "", "desc": ""},
                  {"name": "", "default": "", "required": "", "type": "", "desc": ""}
                  ],
         "integration": "na",
         "instance": "na",
         "access_instructions": "",
         "limitations": []
         }
    """

def test_doc_n_batch():
    print("I halped")
    pass

def doc_and_batch_help(func_name=None, debug=False):
    if debug:
        print("Running with debug")

    title = "Documentation and Batch Helpers"
    help_func = "doc_and_batch_help"
    exp_func = "batch_list_in"

    doc_functions = {
    "general utility": [
        "batch_list_in",
        "batch_by_date",
        "df_expand_col",
        "make_list_like_any"
    ],
    "date handling": [
        "resolve_start_date",
        "handle_dates",
        "range_dates",
        "range_hist"
    ]
    }


    main_help(title, help_func, doc_functions, globals(), exp_func=exp_func, func_name=func_name, debug=debug)
    loaded_helpers.append("doc_and_batch")


def main_help(title, help_func, func_dict, myglobals, exp_func="my_awesome_function", func_name=None, debug=False):


    if func_name is not None:
        if isfunction(func_name):
            func_name = func_name.__name__

    if func_name is None:
        out_md = ""
        out_md += f"# {title} Include File\n"
        out_md += "--------------------\n"
        out_md += "To view this help type:\n\n"
        out_md += f"`{help_func}()`\n\n"
        out_md += "\n"
        out_md += "To view the help for a specific function type:\n\n"
        out_md += f"`{help_func}('function_name')`\n\n"
        out_md += "Example:\n\n"
        out_md += f"`{help_func}('{exp_func}')`\n\n"
        out_md += "\n"
        out_md += "## Helper Categories\n"
        out_md += "---------------------\n"
        for cat in func_dict.keys():
            out_md += f"### {cat}\n"
            out_md += "-------------------------\n"
            out_md += "| function | description | Default list_field | function loaded | query function |\n"
            out_md += "| -------- | ----------- | ------------------- | --------------- | -------------- |\n"
            for f in func_dict[cat]:
                myQ = is_query_func(f, myglobals, debug=debug)
                myFound = function_in_kernel(f, myglobals)
                mylistfield = get_list_field(f, myglobals)
                if myQ is None:
                    myQ = ""
                out_md += f"| {f} | {get_func_doc_item(f, 'desc', myglobals, debug=debug)} | {mylistfield} | {myFound} | {myQ} |\n"
            out_md += "\n"
        display(Markdown(out_md))
    elif func_name=="basic":
        out_md = ""
        out_md += f"### {title} Include File Loaded\n"
        out_md += f"Type `{help_func}()` to see extended help and available functions/queries\n\n"
        display(Markdown(out_md))
    else:
        parse_docs(func_name, myglobals, debug=debug)





######################################################################################################################################################
###################################################################
# general utility
# Documentation: Complete
#
def batch_list_in(batchlist, base_query, integration, instance, batchsize=500, list_quotes='single', list_sep=', ', dedupe=True, remove_none=True, debug=False):
    """ {"name": "batch_list_in",
         "desc": "Take in a query, list, integration, and instance and split the list up into batched, returning all results as one dataframe",
         "return": "A dataframe with the result of all batches combined",
         "examples": ["combined_df = batch_list_in(ip_list, ip_query, 'impala', 'prod')"],
         "args": [{"name": "batchlist", "default": "None", "required": "True", "type": "list", "desc": "List of items to be batched and queried"},
                  {"name": "base_query", "default": "None", "required": "True", "type": "string", "desc": "Query that is complete except for the string ~~here~~ which will be replaced with the current batch"},
                  {"name": "integration", "default": "None", "required": "True", "type": "string", "desc": "The integration the query will be submitted to (i.e. splunk, tera, impala)"},
                  {"name": "instance", "default": "None", "required": "True", "type": "string", "desc": "The instance of the previously provided integration that will be used (i.e. prod, dev)"},
                  {"name": "batchsize", "default": "500", "required": "False", "type": "integer", "desc": "The max number of items in a batch."},
                  {"name": "list_quotes", "default": "single", "required": "False", "type": "string", "desc": "Whether to use single or double quotes on list items. Single is default best for SQLish, double may work better for Splunk types"},
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


    ipy = get_ipython()

    if debug:
        print("Running query using %s instance %s" % (integration, instance))

    if base_query.find("~~here~~") < 0:
        print("Need to know where to the batched list, your query must have '~~here~~' in it like party_id in (~~here~~) if you are doing a list of party ids")
        return pd.DataFrame()

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
    print("Total Items in Batchlist: %s" % list_cnt)

    curs = 0
    next_run = True
    out_df = pd.DataFrame()
    loops = 0
    results_var = "prev_%s_%s" % (integration, instance)

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
        else:
            print("Error must use single or double as your list_quotes")

        print("Batch: %s - %s - %s" % (stidx, enidx, this_len))
        this_query = base_query.replace("~~here~~", this_str)
        try:
            del ipy.user_ns[results_var]
        except:
            pass
        if debug:
            print("")
            print("Cur Query")
            print(this_query)
        ipy.run_cell_magic(integration, instance + " -d", this_query)
        try:
            these_df = ipy.user_ns[results_var]
        except:
            these_df = pd.DataFrame()
            print("Error on batch")
        out_df = pd.concat([out_df, these_df], ignore_index=True)
        print(f"{len(these_df)} results in list batch {loops} - total: {len(out_df)}")
        these_df = None
    return out_df


def batch_by_date(base_query, integration, instance, list_items, date_batch_type, date_start, date_end, range_batchdays=30, range_datefield="asofdate", range_add_ts=False, hist_str="_hs_", hist_format="%Y%m", hist_current_str= "_ct", hist_date_clauses=[], batchsize=500, print_only=False, debug=False):
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
                  {"name": "range_datefield", "default": "asofdate", "required": "False", "type": "string", "desc": "Name of datefield to replace in where clause"},
                  {"name": "range_add_ts", "default": "False", "required": "False", "type": "boolean", "desc": "Add ' 00:00:00' to dates for Teradata timestamps"},
                  {"name": "hist_str", "default": "_hs_", "required": "False", "type": "string", "desc": "Static string on history tables if using hist"},
                  {"name": "hist_format", "default": "%Y%m", "required": "False", "type": "string", "desc": "Date format for hist tables (%Y%m and %y%m supported)"},
                  {"name": "hist_current_str", "default": "_ct", "required": "False", "type": "string", "desc": "String for the current table if using hist"},
                  {"name": "hist_date_clauses", "default": "[]", "required": "False", "type": "list", "desc": "A list of 4 item lists that can be used to replace parts of the query based on the hist date - Careful"},
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
            print(f"Loop {loops} running for Dates {dl}")
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
            if range_add_ts:
                t_d_start = f"{t_d_start} 00:00:00"
                t_d_end = f"{t_d_end} 00:00:00"

            print(f"Loop {loops} running for Dates {t_d_start} to {t_d_end}")
            date_where = f"{range_datefield} >= '{t_d_start}' and {range_datefield} < '{t_d_end}'"
            this_query = base_query.replace("~~date~~", date_where)
        if print_only:
            print_query(this_query, integration, instance)
        else:
            cur_df = pd.DataFrame()
            cur_df = batch_list_in(list_items, this_query, integration, instance, batchsize=batchsize, debug=debug)
            if len(cur_df) > 0:
                out_df = pd.concat([out_df, cur_df], ignore_index=True)
                print(f"{len(cur_df)} results in date batch {loops} - total: {len(out_df)}")
            else:
                print(f"No results on {loops} batch")
    return out_df

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

#####################################################################################################################################################
###################################################################
# Display/Doc Functions
# Documentation: In progress
#



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


def get_func_doc_item(func_name, keyname, myglobals, debug=False):
    if debug:
        de = True
        s = False
    else:
        de = False
        s = True

    doc_dict = parse_docstr(func_name, myglobals, display_error=de, silent=s, debug=debug)
    if doc_dict is not None:
        if keyname in doc_dict:
            retval = doc_dict[keyname]
        else:
            retval = None
            if not s:
                print(f"{keyname} not in docdict")
    else:
        retval = None
        if not s:
            print(f"Unable to parse {func_name} docstring")
    return retval


def is_query_func(func_name, myglobals, debug=False):
    bQueryFunc = None
    doc_dict = parse_docstr(func_name, myglobals, display_error=False, silent=True, debug=debug)
    if doc_dict is not None:
        bQueryFunc = False
        for a in doc_dict['args']:
            if a['name'] == 'print_only':
                bQueryFunc = True
                break
    return bQueryFunc

def get_list_field(func_name, myglobals, debug=False):
    retval = "NA"
    doc_dict = parse_docstr(func_name, myglobals, display_error=False, silent=True, debug=debug)
    if doc_dict is not None:
        for a in doc_dict['args']:
            if a['name'] == 'list_field':
                retval = a['default']
                break
    return retval

def function_in_kernel(func_name, myglobals, debug=False):
    bFound = False
    try:
        doc_str = myglobals[func_name].__doc__
        bFound = True
    except:
        if debug:
            print("Not found: here's the globals")
            print(myglobals)

    return bFound

def parse_docstr(func_name, myglobals, display_error=False, silent=False, debug=False):
    bFound = False
    out_md = ""
    bFound = function_in_kernel(func_name, myglobals, debug=debug)
    if bFound:
        doc_str = myglobals[func_name].__doc__
    else:
        out_md += "## Function not found\n"
        out_md += f"Function {func_name} not found in current kernel. Please check to ensure imports worked correctly\n\n"
        doc_dict = None
    if bFound:
        try:
            doc_dict = json.loads(doc_str)
            if debug:
                print("")
                print(doc_dict)
        except Exception as e:
            doc_dict = None
            out_md += "## Function found - Docstrings did not parse\n"
            out_md += f"Function {func_name} exists but the doc strings did not parse properly, therefore we don't have docs\n\n"
            if display_error:
                out_md += "-----------------\n"
                out_md += "Parse Error:\n\n"
                out_md += f"{str(e)}\n\n"
                out_md += f"``` {doc_str} ```\n\n"

    if out_md != "" and not silent:
        display(Markdown(out_md))
    return doc_dict

def parse_docs(func_name, myglobals, debug=False):
    out_md = ""
    bQueryFunc = False
    if debug:
        disp_err = True
    else:
        disp_err = False
    doc_dict = parse_docstr(func_name, myglobals, display_error=disp_err, debug=debug)
    if doc_dict is not None:
        bQueryFunc = is_query_func(func_name, myglobals, debug=debug)

        out_md += f"# {doc_dict['name']}\n"
        out_md += "---------------\n"
        if doc_dict['integration'] != 'na' and doc_dict['instance'] != 'na':
            out_md += f"**Integration:** {doc_dict['integration']} - **Instance(s):** {doc_dict['instance']}\n\n" 
            out_md += "--------------------\n"
        out_md += f"**Description:** {doc_dict['desc']}\n\n"
        out_md += f"**Returns:** {doc_dict['return']}\n\n"
        if doc_dict['access_instructions'] != "na":
            out_md += "------------------\n"
            out_md += f"**Access Instructions:** {doc_dict['access_instructions']}\n\n"
        if bQueryFunc is not None and bQueryFunc == True:
            out_md += f"In addition to print_only, you can print the underlying query by typing: `{doc_dict['name']}([])`\n\n"
        out_md += "------------------------\n"
        if len(doc_dict['examples']) > 0:
            out_md += "**Examples**\n\n"
            out_md += "---------------------\n"
            out_md += "| Example | Notes |\n"
            out_md += "| ------- | ----- |\n"
            for e in doc_dict['examples']:
                ex = ""
                nt = ""
                if isinstance(e, list):
                    ex = e[0]
                    nt = e[1]
                else:
                    if e.find("#") >= 0:
                        ex = e.split("#")[0]
                        nt = e.split("#")[1]
                    else:
                        ex = e
                        nt = "N/A"
                out_md += f"| `{ex}` | {nt} |\n"
            out_md += "\n"
        out_md += "## Arguments\n"
        out_md += "---------------------\n"
        out_md += "| Arg | Req? | Default | Type | Description|\n"
        out_md += "| --- | ---- | ------- | ---- | -----------|\n"
        for a in doc_dict['args']:
            out_md += f"| {a['name']} | {a['required']} | {a['default']} | {a['type']} | {a['desc']} |\n"
        out_md  += "\n"

        if len(doc_dict['limitations']) > 0:
            out_md += "### Limitations\n"
            out_md += "------------\n"
            for l in doc_dict['limitations']:
                out_md += f"- {l}\n"
    if debug:
        print("out_md:")
        print(out_md)
    if out_md != "":
        display(Markdown(out_md))


def print_query(q, integ, inst, retval=False):
    print("")
    print("Replace ~~here~~ with a list of the item you'd want to search for")
    print("")
    p_val = f"\n%%{integ} {inst}\n{q}"
    if retval:
        return p_val
    else:
        print(f"\n%%{integ} {inst}\n{q}")
