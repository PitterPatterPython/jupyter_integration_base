# Doc Functions
from IPython.display import display, Markdown
import datetime
import json
import sys
import os
import operator
from inspect import isfunction
import pandas as pd
# This is the first helper loaded. It has to instantiate loaded_helpers, but if it exists, we want to leave it as is
try:
    if not isinstance(loaded_helpers, list):
        loaded_helpers = []
except:
    loaded_helpers = []

load_name = "function_doc"
if load_name not in loaded_helpers:
    loaded_helpers.append(load_name)



# NOTE: These functions are not to be called by users


def function_doc_help(func_name=None, debug=False):
    if debug:
        print("Running with debug")

    title = "Function Documentation Helpers"
    help_func = "function_doc_help"
    exp_func = "parse_docs"

    doc_functions = {
        "Display": [
            "parse_docs"
        ]
    }


    main_help(title, help_func, doc_functions, globals(), exp_func=exp_func, func_name=func_name, debug=debug)



def load_doc_to_loaded_fx(parsed_func, this_ipy=None, debug=False):
    non_jlab = False
    this_name = parsed_func['name']
    if this_ipy is not None:
        my_ipy = this_ipy
        if "loaded_fx" not in my_ipy.user_ns:
            if debug:
                print("loaded_fx not found in my_ipy user_ns")
            my_ipy.user_ns["loaded_fx"] = {}
    else:
        non_jlab = True
    if non_jlab:
        if debug:
            print("Appears to be non jupyter lab")
        # This doesn't appear to be jupyter lab, we will try to grab a global named loaded_fx and put it there, otherwise *shrug*
        global loaded_fx
        if loaded_fx is None:
            loaded_fx = {}
        if isinstance(loaded_fx, dict):
            loaded_fx[this_name] = parsed_func
    else:
        my_ipy.user_ns["loaded_fx"][this_name] = parsed_func


def load_fx_list_to_loaded_fx(fx_list, this_ipy=None, debug=False):
    if this_ipy is not None:
        lookup = this_ipy.user_ns
    else:
        lookup = globals()

    for fx in fx_list:
        try:
            this_fx = lookup[fx]
        except Exception as e:
            this_fx = None
            if debug:
                print(f"Trying to load {fx} got error: {e}")
        if isfunction(this_fx) and this_fx.__doc__:
            this_doc = this_fx__doc__.strip()
            prob_sharedfx = False
            if debug:
                print(f"For {fx} prob_sharedfx: {prob_sharedfx}")
            if this_doc.find('{"name":') == 0:
                prob_sharedfx = True
            if prob_sharedfx:
                try:
                    this_func_doc = json.loads(this_doc)
                    if debug:
                        print("this_func_doc loaded")
                except Exception as e:
                    print(f"For {fx}, it's probably a sharedfx and we have an error loading function docs: {e}")
                    this_func_doc = {"name": fx, "group": "load_errors", "desc": f"Error Loading Docs: {e}", "raw_docs": this_doc}
                load_doc_to_loaded_fx(this_func_doc, this_ipy=this_ipy, debug=debug)


def main_help(title, help_func, func_dict, myglobals, exp_func="my_awesome_function", func_name=None, magic_src=None, debug=False):


    if func_name is not None:
        if isfunction(func_name):
            func_name = func_name.__name__

    if func_name is None:
        out_md = ""
        if magic_src is None:
            out_md += f"# {title} Include File\n"
        else:
            out_md += f"# {title} magic %{magic_src}\n"
        out_md += "--------------------\n"
        out_md += "To view this help type:\n\n"
        if magic_src is None:
            out_md += f"`{help_func}()`\n\n"
        else:
            out_md += f"`%{magic_src} functions`\n\n"


        out_md += "\n"
        out_md += "To view the help for a specific function type:\n\n"
        if magic_src is None:
            out_md += f"`{help_func}('function_name')`\n\n"
            out_md += "Example:\n\n"
            out_md += f"`{help_func}('{exp_func}')`\n\n"
        else:
            out_md += f"`%{magic_src} functions function_name`\n\n"
            out_md += "Example:\n\n"
            out_md += f"`%{magic_src} functions {exp_func}`\n\n"

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
        if magic_src is None:
            out_md += f"**{title} Include File Loaded**\n"
            out_md += f"Type `{help_func}()` to see extended help and available functions/queries\n\n"
        else:
            out_md += f"**{title} magic %{magic_src} Loaded**\n"
            out_md += f"Type `%{magic_src} functions` to see extended help and available functions/queries\n\n"
            
        display(Markdown(out_md))
    else:
        parse_docs(func_name, myglobals, debug=debug)

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
            out_md += f"In addition to print_only, you can print the underlying query by typing: `{doc_dict['name']}([])` or `{doc_dict['name']}()`\n\n"
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
