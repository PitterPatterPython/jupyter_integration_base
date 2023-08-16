#!/usr/bin/python

from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from pyvis_core._version import __desc__
@magics_class
class Pyvis(Magics):
    # Static Variables
    # The name of the integration
    name_str = "pyvis"
    magic_name = name_str
    debug = False
    # {name_str}_base is used for first load
    # {name_str}_full is used after first load


    def __init__(self, shell, debug=False, *args, **kwargs):
        super(Pyvis, self).__init__(shell, debug=debug)
        self.debug = debug

        # Check namespace for integration and addon dicts
        if "jupyter_loaded_integrations" not in self.shell.user_ns:
            if self.debug:
                print("jupyter_loaded_integrations not found in ns: adding")
            self.shell.user_ns['jupyter_loaded_integrations'] = {}
        if "jupyter_loaded_addons" not in self.shell.user_ns:
            if self.debug:
                print("jupyter_loaded_addons not found in ns: adding")
            self.shell.user_ns['jupyter_loaded_addons'] = {}

        # Check to see if our name_str is in loaded addons (it shouldn't be)
        if self.name_str in self.shell.user_ns['jupyter_loaded_addons']:
            print(f"Potenital Multiverse collision of names: {self.name_str}")
            print(self.shell.user_ns['jupyter_loaded_addons'])
        else:
            # This is where add our base version
            self.shell.user_ns['jupyter_loaded_addons'][self.name_str] = f"{self.name_str}_base"

    # This returns the description
    def retCustomDesc(self):
        return __desc__

    # The line cell magic to fully load this integrations

    @line_cell_magic
    def pyvis(self, line, cell=None):
        if not self.name_str in self.shell.user_ns['jupyter_loaded_addons']:
            print(f"Somehow we got here and {self.name_str} is not in loaded addons - Unpossible")
        else:
            if self.shell.user_ns['jupyter_loaded_addons'][self.name_str] != f"{self.name_str}_base":
                print(f"We should only get here with a {self.name_str}_base state. Currently for {self.name_str}: {self.shell.user_ns['jupyter_loaded_addons'][self.name_str]}")
            else:
                if self.debug:
                    print(f"Loading full {self.name_str} from base")
                full_load = f"from {self.name_str}_core.{self.name_str}_full import {self.name_str.capitalize()}\n{self.name_str}_full = {self.name_str.capitalize()}(ipy, debug={str(self.debug)})\nipy.register_magics({self.name_str}_full)\n"
                if self.debug:
                    print("Load Code: {full_load}")
                self.shell.ex(full_load)
                self.shell.user_ns['jupyter_loaded_addons'][self.name_str] = f"{self.name_str}_full"
                self.shell.run_cell_magic(self.name_str, line, cell)

