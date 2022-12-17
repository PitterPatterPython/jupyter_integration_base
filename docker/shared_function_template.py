# Put any imports your functions need up here
import datetime


# You can change the name of your help function here (highly recommended to use the _help suffix on your shared function files)
def shared_function_help(func_name=None, debug=False):



    # Variables
    title = "Shared Function Template File"     # The title of this shared function file. (Good to group them, queries, features, enrichment, utility etc)
    help_func = "shared_function_help"          # The name of the help function (i.e. this function i.e shared_function_help)
    exp_func = "ret_square"                     # An example function you can use to demostrate how to get help on a function (It should exist below)
    functions_name = "shared_function_template" # The name of this file you can use in other files to check if this one is loaded (if there are dependent functions



    #
    # Function Dictionary
    #
    # This is the list of functions you are sharing.
    # Each dictionary key is a group title, and then the value is list of the function names.
    # This has to be changed if you want to add a function into the listed functions in the help file
    #
    doc_functions = {

        "math functions": [
            "ret_square",
            "add_self"
        ],
        "query functions": [
            "example_query",
        ]
    }


# Do not change the rest of this function
    if debug:
        print("Running with debug")

    main_help(title, help_func, doc_functions, exp_func=exp_func, func_name=func_name, debug=debug)
    if functions_name not in loaded_helpers:
        loaded_helpers.append(functions_name)

########## Start Functions ###########################
# This is where the functions are listed

def ret_square(item_2_sqr, times_2_sqr=1, debug=False):
    """ {"name": "ret_square",
         "desc": "Take any integer, and square it times_2_sqr (defaults to 1) times and return that value",
         "return": "An integer with the results",
         "examples": ["squared_item = ret_square(2) # Returns 4", squared_item = ret_square(2, times_2_sqr=2) # Returns 16"],
         "args": [{"name": "item_2_sqr", "default": "None", "required": "True", "type": "int", "desc": "Item to Square"},
                  {"name": "time_2_sqr", "default": "1", "required": "False", "type": "int", "desc": "The number of times the item should be squared"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Turns on debug messages"}
                  ],
         "integration": "Any",
         "instance": "Any",
         "access_instructions": "na",
         "limitations": ["Only works on integers"]
         }
    """

    out_val = item_2_sqr

    if debug:
        print("Debug is on!")

    for i in range(times_2_sqr):
        out_val = out_val * out_val

    return out_val

def add_self(item_2_add,  debug=False):
    """ {"name": "add_self",
         "desc": "Take any integer, and add it to itself",
         "return": "An integer with the results",
         "examples": ["added_item = add_self(2) # Returns 4"],
         "args": [{"name": "item_2_add", "default": "None", "required": "True", "type": "int", "desc": "Item to Add"},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Turns on debug messages"}
                  ],
         "integration": "Any",
         "instance": "Any",
         "access_instructions": "na",
         "limitations": ["Only works on integers"]
         }
    """

    out_val = item_2_add + item_2_add

    if debug:
        print("Debug is on!")


    return out_val

def example_query(list_items=[], list_field="myid", myop="IN", date_start=None, date_end="now", batchsize=500, print_only=False, debug=False):
    """ {"name": "example_query",
         "desc": "An example of query documentation",
         "return": "Dataframe with full results",
         "examples": ["result_df = example_query(['12345', '23456'], date_start='2022-06-01')", "result_df = example_query(['123456', '12345678'], list_field="phone_num", date_start='2022-11-01', date_end='2022-12-01', batch_size=1000, print_only=False, debug=True)"],
         "args": [{"name": "list_items", "default": "[]", "required": "False", "type": "list", "desc": "List of items to add to query and replace ~~here~~ with. IF empty list or not provided, it will default to printing the query"},
                  {"name": "list_field", "default": "myid", "required": "False", "type": "string", "desc": "The field name to run the batch list against. Can be overloaded to add minor filters"},
                  {"name": "myop", "default": "IN", "required": "False", "type": "string", "desc": "The operation to use. Defaults to IN but some DBMSs support things like LIKE ANY or LIKE ALL"},
                  {"name": "date_start", "default": "None", "required": "False", "type": "string or None", "desc": "The date to start the query with. If None, defaults to 3 months before today"},
                  {"name": "date_end", "default": "now", "required": "False", "type": "string", "desc": "The date to end the query, defaults to now (today)"},
                  {"name": "batchsize", "default": "500", "required": "False", "type": "int", "desc": "The size of the batches. If the list_items exceeds this, it will break it up into pieces"},
                  {"name": "print_only", "default": "False", "required": "False", "type": "boolean", "desc": "Do not run the query, just print it."},
                  {"name": "debug", "default": "False", "required": "False", "type": "boolean", "desc": "Turns on debug messages"}
                  ],
         "integration": "impala",
         "instance": "prod",
         "access_instructions": "Access to the Database through the impala prod integration and instance",
         "limitations": ["This only applies to a impala instance named prod. This is for examples only."]
         }
    """

    myname = sys._getframe().f_code.co_name
    integration = get_func_doc_item(myname, "integration")
    instance = get_func_doc_item(myname, "instance")

    date_start = resolve_start_date(date_start)
    out_df = None
    if len(list_items) == 0:
        print_only = True

    base_query = f"""select myid, cust_date, phone_num, some_name, winner_winner, chicken_dinne
from
mybest_db.mybest_table
where
(~~date~~)
and {list_field} {myop} (~~here~~)
"""

    if date_end == "now":
        date_str = f"cust_date >= '{date_start}'"
    else:
        date_str = f"cust_date >= '{date_start}' and cust_date < '{date_end}'"
    this_query = base_query.replace("~~date~~", date_str)

    if print_only:
        print_query(this_query, integration, instance)
    else:
        out_df = batch_list_in(list_items, this_query, integration, instance, batchsize=batchsize, debug=debug)
    return out_df



######### End Functions ############################

# Call Basic help on first load so users know it's been loaded

shared_function_help("basic")
