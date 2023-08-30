#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
from collections import OrderedDict
from pathlib import Path
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

import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import getpass
from namedpw_core._version import __desc__

@magics_class
class Namedpw(Addon):
    # Static Variables

    key_name = "stop"
    namedpw_dir = None
    magic_name = "namedpw"
    name_str = "namedpw"
    enc_secrets_dict = {}

    custom_evars = ['namedpw_addon_dir']

    custom_allowed_set_opts = ['namedpw_addon_dir']

    myopts = {}
    myopts['namedpw_addon_dir'] = ['~/.ipython/integrations/' + name_str, "Directory for key storage caching/configs"]


    def __init__(self, shell, debug=False,  *args, **kwargs):
        super(Namedpw, self).__init__(shell, debug=debug)
        self.debug = debug


        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]
        self.load_env(self.custom_evars)

        if self.namedpw_dir is None:
            self.set_namedpw_dir()
        self.refresh_secrets_dict()

# Display Help can be customized

# Key Management

    def get_key(self):
        # This function returns the current kernel named pass key. If it doesn't exist, it generates it and returns it
        if not self.key_name in self.ipy.user_ns:
            if self.debug:
                print("Namepw key named %s not in user_ns - Generating" % self.key_name)
            self.gen_key()
        return self.ipy.user_ns[self.key_name]

    def gen_key(self):
        tkey = Fernet.generate_key()
        self.ipy.user_ns[self.key_name] = tkey


    def get_key_from_pass(self, mypassword):
        password_provided = mypassword  # This is input in the form of a string
        password = password_provided.encode()  # Convert to type bytes
        salt = b'salt_super_salty'  # I recognize that this isn't super strong, but it provides enough cover on the salt
        kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))  # Can only use kdf once
        return key


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
        myencpass = self.enc_data(tpass)
        pw_list[namedpw] = myencpass
        del self.ipy.user_ns['tpass']
        del tpass

    def get_named_PW(self, namedpw):
        pw_list = self.get_PW_list()
        cur_key = self.get_key()
        if namedpw not in pw_list.keys():
            self.set_named_PW(namedpw)
            pw_list = self.get_PW_list()
        tpass = self.dec_data(pw_list[namedpw])
        return tpass


    def clear_named_PW(self, namedpw):
        pw_list = self.get_PW_list()
        if namedpw in pw_list.keys():
            print("Clearing password for namedpw %s" % namedpw)
            del pw_list[namedpw]
        else:
            print("Named password %s does not exist - Password not cleared" % namedpw)

    def clear_secret(self, secret_name):
        pwname = secret_name + "_npw"
        print("Also clearing named password: %s" % pwname)
        self.clear_named_PW(pwname)
        secret_path = Path(str(self.namedpw_dir) + "/skrt_" + secret_name + ".enc")
        if os.path.exists(secret_path):
            os.remove(secret_path)
            print("Secret %s cleared!" % secret_name)
        else:
            print("Secret %s not found" % secret_name)
        self.refresh_secrets_dict()



    def customHelp(self, curout):
        n = self.name_str
        m = "%" + self.name_str
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout
        out += table_header
        out += "| %s | Save named password yournamedpw in current kernel |\n" % (m + " save password yournamedpw")
        out += "| %s | Clear named password yournamedpw in current kernel |\n" % (m + " clear password yournamedpw")
        out += "| %s | List the names of currently saved named passwords |\n" % (m + " list passwords")
        out += "| %s | Save secret yoursecret |\n" % (m + " save secret yoursecret")
        out += "| %s | Clear secret yoursecret |\n" % (m + " clear secret yoursecret")
        out += "| %s | List the names of currently saved secrets |\n" % (m + " list secrets")
        out += "\n\n"
        return out

    def retCustomDesc(self):
        return __desc__

    def list_items(self, list_type="passwords"):
        print("")
        if list_type == "passwords":
            print("Currently Defined Named %s:" % list_type.capitalize())
            print("---------------------")
            list_dict = self.get_PW_list()
        elif list_type == "secrets":
            print("Currently Defined %s:" % list_type.capitalize())
            print("---------------------")
            self.refresh_secrets_dict()
            list_dict = self.enc_secrets_dict
        else:
            print("Unknown list type - Not doing anything")
            list_dict = {}
        for pw in list_dict.keys():
                print(pw)
        print("")
    def set_namedpw_dir(self):
        tstorloc = self.opts['namedpw_addon_dir'][0]
        if tstorloc[0] == "~":
            myhome = jiu.getHome(debug=self.debug)
            thome = tstorloc.replace("~", myhome)
            if self.debug:
                print(thome)
            tpdir = Path(thome)
        else:
            tpdir = Path(tstorloc)
        if self.debug:
            print(tpdir)
        self.namedpw_dir = tpdir

        if not os.path.isdir(self.namedpw_dir):
            os.makedirs(self.namedpw_dir)

    def refresh_secrets_dict(self):
        self.enc_secrets_dict = {}

        for f in os.listdir(self.namedpw_dir):
            if f.find("skrt_") == 0:
                tskrt = f.replace("skrt_", "").replace(".enc", "")
                tskrt_val = None
                try:
                    sfile_path = Path(str(self.namedpw_dir) + "/" + f)
                    sfile = open(sfile_path, "rb")
                    tskrt_val = sfile.read()
                    sfile.close()
                except Exceptions as e:
                    if self.debug:
                        print("Found Secret File: %s - but could not read - Error: %s" % (f, str(e)))
                    tskrt_val = None
                if tskrt_val is not None:
                    self.enc_secrets_dict[tskrt] = tskrt_val

###############################


    def get_saved_secret(self, secret_name):
        self.refresh_secrets_dict()
        if secret_name not in self.enc_secrets_dict:
            print("Secret name: %s not defined - Setting secret now!" % secret_name)
            self.set_saved_secret(secret_name)
        secret_pass = self.get_named_PW(secret_name + "_npw")
        dec_secret = self.read_secret(secret_name, secret_pass)

        return dec_secret

    def set_saved_secret(self, secret_name):
        print("")
        print("We are setting or replacing the value for the saved secret %s - What you will need:" % secret_name)
        print(" - The value of the secret. (This is not saved to disk unencrypted)")
        print(" - A password to encrypt the secret with")
        print("")
        print("NOTE: There is no recoverability if you forget the password - Secret Accordingly")
        print("")

        print("Please paste the raw text of the secret with name %s that you wish to save:" % secret_name)
        tsecret = ""
        self.ipy.ex("from getpass import getpass\ntpass = getpass(prompt='Secret Value: ')")
        tsecret = self.ipy.user_ns['tpass']
        del self.ipy.user_ns['tpass']
        print("")
        secret_named_pw = secret_name + "_npw"
        pw_list = self.get_PW_list()
        if secret_named_pw in pw_list.keys():
            print("Named PW %s is already defined, we are going to clear it to reset the secret: %s" % (secret_named_pw, secret_name))
            self.clear_named_PW(secret_named_pw)

        print("Now please enter the password for secret %s. It will be usable as %s" % (secret_name, secret_named_pw))
        tpass = self.get_named_PW(secret_named_pw)

        self.save_secret(tsecret, secret_name, tpass)
        tsecret = None
        tpass = None
        del tsecret
        del tpass

    def save_secret(self, secret, secret_name, secret_pass):

        enc_secret = self.enc_data(secret, key_text=secret_pass)
        secret_path = Path(str(self.namedpw_dir) + "/skrt_" + secret_name + ".enc")
        f = open(secret_path, "wb")
        f.write(enc_secret)
        f.close()


    def read_secret(self, secret_name, secret_pass):
        secret_path = Path(str(self.namedpw_dir) + "/skrt_" + secret_name + ".enc")
        f = open(secret_path, "rb")
        enc_secret = f.read()
        f.close()
        secret = self.dec_data(enc_secret, key_text=secret_pass)
        return secret


    def enc_data(self, mydata, key_text=None):
        if key_text is None:
            cur_key = self.get_key()
        else:
            cur_key = self.get_key_from_pass(key_text)

        tenc = Fernet(cur_key)
        tencdata = tenc.encrypt(mydata.encode('utf-8'))
        return tencdata

    def dec_data(self, myedata, key_text=None):
        if key_text is None:
            cur_key = self.get_key()
        else:
            cur_key = self.get_key_from_pass(key_text)

        tenc = Fernet(cur_key)
        try:
            tdecdata = tenc.decrypt(myedata).decode('utf-8')
        except Exception as e:
            print("Password/Secret Decryption failed")
            print(str(e))
            tdecdata = None
        return tdecdata


###############################

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
                if line.lower().strip().find("clear password") == 0:
                    self.clear_named_PW(line.replace("clear password", "").strip())
                elif line.lower().strip().find("save password") == 0:
                    self.set_named_PW(line.replace("save password", "").strip())
                elif line.lower().strip().find("list passwords") == 0:
                    self.list_items(list_type="passwords")
                elif line.lower().strip().find("clear secret") == 0:
                    self.clear_secret(line.replace("clear secret", "").strip())
                elif line.lower().strip().find("save secret") == 0:
                    self.set_saved_secret(line.replace("save secret", "").strip())
                elif line.lower().strip().find("list secrets") == 0:
                    self.list_items(list_type="secrets")
                elif line.lower().strip().find("list") == 0:
                    self.list_items(list_type="passwords")
                    self.list_items(list_type="secrets")
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)
