print("Example Shared Module for Documentation Demo") 

from mymod.mymath.maths import mysum
from mymod.mystrings.strings import myconcat

from mymod.mymath.mymulty.multi import multi_func
from mymod.mymath.mydiv.div import div_func

from mymod.base import doc_format

def doc_funcs():
    """Base Function Indicating this is a Documented Function for use with integrations
    returns True
    """
    return True

