# Put any imports your functions need up here
import datetime

###########################################3
# Note about these files
#
# This is an example shared function file.  So I can demonstrate it, I copy it to a ~/Notebooks directory that I know will be mapped into the docker container.
# In reality, these work best on a shared drive for a team. (In Windows you can call via UNCs to not have the different drive name mess you up)
# Even better, you'd have them stored in a repo and as part of the push process for new updates, you copy to a shared folder so it updates for everyone.
#
# Some other notes:
# - I put an example of how to call these in %helloworld go
#   - This is where you connect to DBs and add any sort of shared function files you may have
# - You can have any number of shared function files. Group them by need, queries, features, pivots, utility etc.
# - The query functions work great for documenting the main functions people use. It's better than everyone having their own text file of queries.
# - The functions for printing function documentation and for batching of queries exists in jupyter_integration_base/helloword_core/doc_and_batch.py
# - doc_and_batch help files can also be viewed by typing %helloworld doc_and_batch
#


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

    main_help(title, help_func, doc_functions, globals(), exp_func=exp_func, func_name=func_name, debug=debug)
    if functions_name not in loaded_helpers:
        loaded_helpers.append(functions_name)

########## Start Functions ###########################
# This is where the functions are listed

# A basic function that doesn't do anything fancy with databases, integrations, or instances
# Can still be real handy

def ret_square(item_2_sqr, times_2_sqr=1, debug=False):
    """ {"name": "ret_square",
         "desc": "Take any integer, and square it times_2_sqr (defaults to 1) times and return that value",
         "return": "An integer with the results",
         "examples": ["squared_item = ret_square(2) # Returns 4", "squared_item = ret_square(2, times_2_sqr=2) # Returns 16"],
         "args": [{"name": "item_2_sqr", "default": "None", "required": "True", "type": "int", "desc": "Item to Square"},
                  {"name": "times_2_sqr", "default": "1", "required": "False", "type": "int", "desc": "The number of times the item should be squared"},
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


# Another basic function to show how the grouping works in the doc_functions dict at the top

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


# A more complex example of a "query" function. These are nice to both put in highly used functions as well as SQL queries on certain data stores you want to document

def example_query(list_items=[], list_field="myid", myop="IN", date_start=None, date_end="now", batchsize=500, print_only=False, debug=False):
    """ {"name": "example_query",
         "desc": "An example of query documentation",
         "return": "Dataframe with full results",
         "examples": [
                        "result_df = example_query(['12345', '23456'], date_start='2022-06-01')",
                        ["result_df = example_query(['123456', '12345678'], list_field='phone_num', date_start='2022-11-01', date_end='2022-12-01', batch_size=1000, print_only=False, debug=True)", "More complex with different list field"],
                        ["example_query([], list_field=\\"some_name = 'John' and phone_num\\", date_start='2022-11-01', date_end='2022-11-15', print_only=True)", "Example overloaded list_field"]
                    ],
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
 
    # This block is needed if you want to pull the integration and instance name in the code
    # Specifically for query functions so you don't have manually type in what integration both in the code and in the documentation
    # It also can be used for other things
    # TODO: We could detect access errors and print out the access_instructions sometime in the future
    # TODO: We also go do an example only output perhaps
    myname = sys._getframe().f_code.co_name
    integration = get_doc(myname, "integration")
    instance = get_doc(myname, "instance")


    # Start of real function code
    # Create empty output DF
    out_df = None

    # resolve_start_date checks if the date_start is None, if it is, it replaces it with today - 3 months
    date_start = resolve_start_date(date_start)

    # This checks if an empty list was passed (either directly with [] or the function was just called with no arguments, which then sets print_only to true)
    if len(list_items) == 0:
        print_only = True


    # This is the base query used in the function
    # ~~date~~ is where the date string is filled in Lots of ways this can be used more doc comming on this. For this example it just checks a date and fills start_date, and then end date (if it's not now (the default)
    #
    # list_field is replaced with list_field which must have a default TODO: Create better docs on query functions to outline highly used list fields
    #   list_field can also be overloaded to add other (static) criteria to your query. like if you had a cust_active field in your DB, you could set your listfield to be 'cust_active = 1 AND myid' and it would run on the batches, but only for 
    #   cust_active was equal to 1.  If you need more complex queries, just print the query and edit the sql directly
    # myop is the operation used. Mose DBs should use "IN" but some like teradata can use LIKE ANY or LIKE ALL which is really handy
    # ~~here~~ is replaced by the batch_list_in function. If you pass 5000 items in and the batch size is 500, it will run it in 10 batches of 500 and put all the results together for you. 

    base_query = f"""select myid, cust_date, phone_num, some_name, winner_winner, chicken_dinner
from
mybest_db.mybest_table
where
(~~date~~)
and {list_field} {myop} (~~here~~)
"""

    # First we resolve the date_end, and determine what the date  field will be
    # We can do day batching and history table batching.  This is in doc_and batch and is more complex
    if date_end == "now":
        date_str = f"cust_date >= '{date_start}'"
    else:
        date_str = f"cust_date >= '{date_start}' and cust_date < '{date_end}'"
    this_query = base_query.replace("~~date~~", date_str)


    # If print only we only print the query, otherwise we run it through the doc_and_batch batch_list_in function
    if print_only:
        print_query(this_query, integration, instance)
    else:
        out_df = batch_list_in(list_items, this_query, integration, instance, batchsize=batchsize, debug=debug)

    # We return the results (None if print_only was set to True)
    return out_df



######### End Shared Functions ############################


#########################################################
##### get_doc function
# This function must be in every file
# It does not need to be, nor should it be edited
# This function is needed in order get the doc items from globals

def get_doc(func_name, doc_item):
    try:
        retval = get_func_doc_item(func_name, doc_item, globals())
    except:
        retval = "error"
    return retval

########################################################
# And finally, when this file is loaded, call the basic help to let the user know it was loaded
# Call Basic help on first load so users know it's been loaded

shared_function_help("basic")
