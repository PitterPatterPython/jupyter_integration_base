#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
from collections import OrderedDict
import requests
from copy import deepcopy
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Markdown, Javascript, FileLink, FileLinks, Image
import pandas as pd
# Widgets
from ipywidgets import GridspecLayout, widgets
import jupyter_integrations_utility as jiu
from addon_core import Addon

import cryptography
from cryptography.fernet import Fernet


@magics_class
class Namedpw(Addon):
    # Static Variables

    key_name = "stop"

    magic_name = "namedpw"
    name_str = "namedpw"
    custom_evars = []

    custom_allowed_set_opts = []


    myopts = {}


    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Namedpw, self).__init__(shell, debug=debug)
        self.debug = debug

        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)
#        shell.user_ns['profile_var'] = self.creation_name

# Display Help can be customized

# Key Management

    def get_key(self):
        # This function returns the current kernel named pass key. If it doesn't exist, it generates it and returns it
        if not self.key_name in self.ipy.user_ns:
            if self.debug:
                print("Namepw key named %s not in user_ns - Generating" % self.key_name)
            self.gen_key()
        return self.ipy.user_ns[key_name]

    def gen_key(self):
        tkey = Fernet.generate_key()
        self.ipy.user_ns[self.key_name] = tkey


    def get_PW_list(self):
        if not "in_list" in self.ipy.user_ns:
            self.ipy.user_ns["in_list"] = {}
        return self.ipy.user_ns["in_list"]

    def set_named_PW(self, namedpw):
        pw_list = self.get_PW_list()
        cur_key = self.get_key()
        if namedpw in pw_list.keys():
            print("")
            print("* CHANGING Named Password: %s" % namedpw)
            print("")

        print("Please enter the password for named password: %s" % namedpw)
        tpass = ""
        self.ipy.ex("from getpass import getpass\ntpass = getpass(prompt='Named Password: ')")
        tpass = self.ipy.user_ns['tpass']
        myencpass = self.enc_PW(tpass)
        pw_list[namedpw] = myencpass
        del self.ipy.user_ns['tpass']
        del tpass

    def get_named_PW(self, namedpw):
        pw_list = self.get_PW_list()
        cur_key = self.get_key()
        if namedpw not in pw_list.keys():
            self.set_named_PW(namedpw)
            pw_list = self.get_PW_list()
        tpass = self.dec_PW(pw_list[namedpw])
        return tpass

    def enc_PW(self, pw):
        cur_key = self.get_key()
        tenc = Fernet(cur_key)
        tencpass = tenc.encrypt(pw.encode('utf-8'))
        return tencpass

    def dec_PW(self, epw):
        cur_key = self.get_key()
        tenc = Fernet(cur_key)
        try:
            tdecpass = tenc.decrypt(epw).decode('utf-8')
        except Exception as e:
            print("Password Decryption failed")
            print(str(e))
            tdecpass = None
        return tdecpass

    def clear_named_PW(self, namedpw):
        pw_list = self.get_PW_list()
        if namedpw in pw_list.keys():
            print("Clearning password for namedpw %s" % namedpw)
            del pw_list[namedpw]
        else:
            print("Named password %s does not exist - Password not cleared" % namedpw)

    def customHelp(self, curout):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout
        out += table_header
        out += "| %s | Enter named password $namedpw in current kernel |\n" % (m + " $namedpw")
        out += "| %s | Clear named password $namedpw in current kernel |\n" % (m + " clear $namedpw")
        out += "\n\n"
        return out

    def retCustomDesc(self):
        out = "The namedpw addon allows you to managed named passwords used for multiple integrations"
        return out





    # This is the magic name.
    @line_cell_magic
    def namedpw(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        #line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if not line_handled: # We based on this we can do custom things for integrations. 
                if line.lower().strip().find("clear") == 0:
                    self.clear_named_PW(line.replace("clear", "").strip())
                elif len(line.strip().split(" ")) == 1:
                    self.set_named_PW(line.strip())
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)
