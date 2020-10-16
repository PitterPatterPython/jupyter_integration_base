#import mymod.mymath
#import mymod.mystrings

#import mymath
#import mystrings
from mymod.mymath.maths import mysum
from mymod.mystrings.strings import myconcat

from mymod.mymath.mymulty.multi import multi_func
from mymod.mymath.mydiv.div import div_func


def doc_funcs():
    """Base Function Indicating this is a Documented Function for use with integrations
    returns True
    """
    return True


def doc_format():
    """doc_format - Example documentation format for integrations

    Description:
        A function that shows an example of document formatting for people developed shared functions

    Written by: 
        John Omernik

    Keywords:
        docs,formatting,integrations

    Call Example:
        myexample = doc_format()

    Arguments:
        None

    Returns:
        string - Formated Help text
    """

    rettext = """func_name - <Put a short one line description here>

    Description:
        <A longer narrative about how the function works. Longer than one liner>
    
    Written by:
        <name of person who wrote it>

    Keywords:
        <comma,separated,list,of,keywords,for,searching>

    Call Example:
        <Put an example of calling your function like: mystr = doc_format() >

    Arguments:
        arg1 - type - req/opt -  Purpose of argument
        arg2 - string - req - Example of a string argument
        arg3 - int - opt (def: default if opt not provided) - Another argument
    
    Returns:
        string - What is in this return value
        int - what is in this return value


    """
    return rettext



