# jupyter_integration_template
A module to help interaction with Jupyter Notebooks any dataset. For exmaples see https://github.com/johnomernik/hive_core


###
This is a python module that helps to connect Jupyter Notebooks to various datasets. 

Here is what it does:
-------[\
- Identifies line and cell magic for based on your keyword. (for example, jupyter_hive uses %hive and %%hive)
- Handles authentication in as sane of a way as possible, including password authentication (and not storing it in the notebook itself)
- (Future) Hook into a password safe to make it even more seamless
- Returns data to a Pandas Dataframe (and also uses BeakerX's awesome table to disaply)
- Provides cusomization options for display, and handline datastore specific items/quirks
- Provides a place to put limits on queries (limits/partitions etc)
- Provides a place to provide documentation built in



After installing this, to instantiate the module so you can use the magicsput this in a cell:

```
from yourthing_core import Yourthing
ipy = get_ipython()
Yourthing = Yourthing(ipy,  pd_use_beaker=True)
ipy.register_magics(Yourthing)
```
