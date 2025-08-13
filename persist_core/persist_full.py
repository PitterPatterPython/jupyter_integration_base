#!/usr/bin/python

from jupyter_server import serverapp
import psutil
import re

# Base imports for all integrations, only remove these at your own risk!
import json
from pathlib import Path
import shutil
import uuid
import sys
import os
import time
from collections import OrderedDict
import requests
from copy import deepcopy
import importlib
import hashlib
import datetime
import pickle
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML
from IPython.display import display_html, display, Markdown, Javascript, FileLink, FileLinks, Image
import pandas as pd
# Widgets
from ipywidgets import GridspecLayout, widgets
import jupyter_integrations_utility as jiu
import pathlib

from persist_core._version import __desc__
import warnings

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except:
    pass



from addon_core import Addon

@magics_class
class Persist(Addon):

    arrow_support = False
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        arrow_support = True
    except:
        pass

    # Static Variables

    magic_name = "persist"
    name_str = "persist"
    custom_evars = ['persist_addon_dir', 'persist_shared_dir']

    custom_allowed_set_opts = ['persist_purge_days', 'persist_purge_data_only', 'persist_auto_purge', 'persist_addon_dir', 'persist_max_queries', 'persist_query_tz', 'persist_shared_dir']

    # Option Format: [ Value, Description]
    # The options for both the base and customer integrations are a little obtuse at first.
    # This is because they are designed to be self documenting.
    # Each option item is actually a list of two length.
    # opt['item'][0] is the actual value if opt['item']
    # p[t['item'][1] is a description of the option and it's use for built in description.

    myopts = {}
    myopts['persist_use_arrow'] = [1, "Use PyArrow if supported, otherwise default to pickle"]
    myopts['persist_shared_expire_days'] = [7, "Number of days to support shared one time load. If file is older than this date, we will delete"]
    myopts['persist_shared_dir'] = ['', "Directory for one-time shared datasets. Defaults to '' which is not set"]
    myopts['persist_purge_days'] = [60, "Number of days to keep queries before purge events occur"]
    myopts['persist_default_pkl_size'] = ['KB', "Units to show pickle sizes in. Defaults to KB (kilobytes), Supported: B, KB, MB"]
    myopts['persist_purge_data_only'] = [0, "When purging, only purge data, full records of df only, just the data part of queries (retain the query)"]
    myopts['persist_auto_purge'] = [0, "When starting integrations, run a check to automaticall purge old data"]
    myopts['persist_addon_dir'] = ['~/.ipython/integrations/' + name_str, "Directory for sharedmod caching/configs"]
    myopts['persist_max_queries'] = [50, "Max number of quries to allow to be stored"]
    myopts['persist_query_tz'] = ['local', "When showing query time, show as local time or utc (values: local or utc)"]


    # Class Init function - Obtain a reference to the get_ipython()
    # We get the self ipy, we set session to None, and we load base_integration level environ variables.


    def __init__(self, shell, debug=False, *args, **kwargs):
        super(Persist, self).__init__(shell, debug=debug)
        self.debug = debug
        self.nbname = None
        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]

        self.load_env(self.custom_evars)
        bs = "\\"
        myshareddir = self.opts['persist_shared_dir'][0]
        if len(myshareddir) > 2:
            if myshareddir[0] == bs and myshareddir[1] != bs:
                self.opts['persist_shared_dir'][0] = bs + myshareddir

        self.loadPersistedDict()

        #shell.user_ns['persist_var'] = self.creation_name


    def retPersisted(self):

        # {"a88167960e644cceb6dfd1531ef2cde0": {"qtime": 1611754956, "pkl_size": 13321, "integration": "Splunk", "instance": "testing", "query": "search myterm='ff', 'notes':'some notes'} # file name is a88167960e644cceb6dfd1531ef2cde0.pkl
        out = ""

        out += "# Currently Persisted Data\n"
        out += "------------------------\n"
        out += "| Id | Saved TS | Saved Size | Int/Inst | Notes | Query |\n"
        out += "| -- | -------  | ---------- | -------- | ----- | ----- |\n"

        for x in self.persist_dict.keys():
            d = self.persist_dict[x]
            mytime = self.retHumanTime(d['qtime'])
            mysize = self.dispSize(d['pkl_size'])
            myquery = d['query'].strip().replace("\n", "<br>")
            mynotes = d['notes'].strip().replace("\n", "<br>")
            myid = str(x).strip()[0:8]
            strsize = str(mysize) + " " + self.opts['persist_default_pkl_size'][0]
            strint = d['integration'] + '/' + d['instance']
            if strint == '/':
                strint = "Dataframe"
            out += "| %s | %s | %s| %s | %s | %s |\n" % (myid, mytime, strsize, strint, mynotes, myquery)
        out += "\n\n"
        return out




    def getPersistDictMD5(self):
        myfile = self.persist_dict_pkl
        fh = open(myfile, 'rb')
        myhash = hashlib.md5(fh.read()).hexdigest()
        fh.close()
        return myhash


    def checkDirs(self):
        if not os.path.isdir(self.persist_dir):
            os.makedirs(self.persist_dir)
        if not os.path.isdir(self.persisted_data_dir):
            os.makedirs(self.persisted_data_dir)
        if not os.path.isdir(self.session_data_dir):
            os.makedirs(self.session_data_dir)


    def dispSize(self, size):
        retsize = 0
        psize = self.opts['persist_default_pkl_size'][0]
        if psize not in ['B', 'KB', 'MB']:
            print("persist_default_pkl size must be B, KB, or MB, defaulting to KB")
            psize = 'KB'
        if psize == "B":
            retsize = size
        elif psize == "KB":
            retsize = size / 1000
        elif psize == "MB":
            retsize = size / 1000000
        return retsize

    def retHumanTime(self, etime):
        rettime = ""

        mytime = self.opts['persist_query_tz'][0]
        if mytime != "local" and mytime != "utc":
            print("persist_query_tz not set to local or utc, defaulting to local")
            mytime = "local"
        if mytime == "local":
            rettime = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(etime))
        elif mytime == "utc":
            rettime = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime(etime))
        return rettime


    def savePersisted(self):
        # Ok for Arrow
        f = open(self.persist_dict_pkl, 'wb')
        # TODO Handle Merges
        pickle.dump(self.persist_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.close()


    def retStorageMethod(self):
        if self.arrow_support and self.opts['persist_use_arrow'][0] == 1:
            if self.debug:
                print("Saving with pyarrow")
            storage_method = "parq"
        elif self.opts['persist_use_arrow'][0] == 1 and not self.arrow_support:
            print("Option to save with arrow selected, however arrow modules not loaded - falling back to savintg with pickle")
            storage_method = "pkl"
        else:
            if self.debug:
                print("Option selected to save with pickle")
            save_method = "pkl"
        return storage_method

    def saveShared(self, mydf):
        bSave = True
        retid = None
        shared_path = self.getSharedPath()
        if shared_path is None:
            bSave = False

        if bSave:
            myid = self.getUUID()
            fname = myid + ".parq"
            sfile = shared_path / fname
            retid = myid
            try:
                mysize = self.saveParquetFile(mydf,sfile)
 #               tmp_arrow = pa.Table.from_pandas(mydf)
 #               pq.write_table(tmp_arrow, sfile)
 #               tmp_arrow = None
                print(f"One-Time Share File created in {shared_path}")
                print(f"Note this will not be accessible after it has been accessed once or after {self.opts['persist_shared_expire_days'][0]} days - which ever comes first")
                print("Shared dataframes is NOT meant for storage of data, only transfer")
                print("")
                retid = myid

            except Exception as e:
                print("Error saving Data")
                print(str(e))
                retid = None

        return retid

    def loadShared(self, myid):
        bLoad = True
        mydf = None

        shared_path = self.getSharedPath()
        if shared_path is None:
            bLoad = False
        else:
            fname = myid + ".parq"
            sfile = shared_path  / fname
            if not os.path.isfile(sfile):
                print("****** WARNING")
                print(f"File for id {myid} doesn't exist or is not accessible - NOT loaded")
                bLoad = False

        if bLoad:
            try:
                tmp_arrow = pq.read_table(sfile)
                mydf = tmp_arrow.to_pandas()
                tmp_arrow = None
            except Exception as e:
                print(f"Load Error for saved id {myid} - NOT loaded")
                print(str(e))
                mydf = None
        return mydf


    def getSharedPath(self):
        shared_path = None
        shared_dir = self.opts['persist_shared_dir'][0]
        if shared_dir != '':
            shared_path = pathlib.Path(shared_dir)
            if not os.path.isdir(shared_path):
                print("****** WARNING")
                print(f"Shared Directory Path: {shared_path} is not a valid directory  - SHARED OPERATIONS DISABLED")
                shared_path = None
            else:
                pass
        else:
            print("Shared Locatio not set - Please set via persist_shared_dir or via ENV variable JUPYTER_PERSIST_SHARED_DIR")
            shared_path = None
        return shared_path


    def procShared(self, line):
        # shared save mydf
        # shared load ID mydf
        shared_path = self.getSharedPath()

        if shared_path is not None:
            cmdlist = line.lower().replace("shared", "").strip().split(" ")
            if cmdlist[0] == "save":
                dfname = cmdlist[1]
                if dfname in self.ipy.user_ns:
                    if isinstance(self.ipy.user_ns[dfname], pd.DataFrame):
                        myid = self.saveShared(self.ipy.user_ns[dfname])
                        if myid is not None:
                            print("To Load Dataframe send the following:\n")
                            print(f"%persist shared load {myid} {dfname}")
                            print("")
                    else:
                        print(f"Provided Dataframe name variable {dfname} is not a valid Pandas Dataframe - Not Saving")
                else:
                    print(f"Dataframe name provided {dfname} is not found in current username namespace - Not Saving")
            elif cmdlist[0] == 'load':
                loadid = cmdlist[1]
                dfname = cmdlist[2]
                if dfname in self.ipy.user_ns:
                    print(f"variable name {dfname} already exists in namespace, not loading")
                else:
                # Try a load
                    this_df = self.loadShared(loadid)
                    if this_df is not None:
                        try:
                            self.ipy.user_ns[dfname] = this_df
                            self.deleteShared(loadid)
                        except Exception as e:
                            prtin(f"Load failed: {str(e)}")
            # Load something
            else:
                print(f"Command provided is not 'save' or 'load' - {cmdlist[0]}")
        else:
            print("Shared Operations Disabled due to Invalid Shared Path")

    def deleteShared(self, myid):
        shared_path = self.getSharedPath()
        if shared_path is not None:
            fname = myid + ".parq"
            sfile = shared_path / fname
            if os.path.isfile(sfile):
                try:
                    os.remove(sfile)
                except Exception as e:
                    print(f"Could not delete file - Error: {str(e)}")
            else:
                print(f"Could not remove shared dataset named {fname} in {shared_path} because file doesn't exist")
        else:
            print("Shared path error, shouldn't get here")


    def saveParquetFile(self, mydf, save_file, mydfname=None):
        mysize = 0
        if self.debug:
            print(f"Saving dataframe with shape {mydf.shape} as {save_file}")
        try:
            tmp_arrow = pa.Table.from_pandas(mydf)
            pq.write_table(tmp_arrow, save_file)
            mysize = os.path.getsize(save_file)
            tmp_arrow = None
        except (pa.ArrowInvalid, TypeError, ValueError) as e:
            print("⚠️ Parquet conversion failed due to incompatible or mixed column types.")
            print(f"Details: {str(e)}")
            mydf_fixed, coerce_warnings = self.coerce_mixed_columns(mydf, sample_size=1000)

            print("")
            print("🔄 Attempting to save after coercing mixed-type columns...")
            for w in coerce_warnings:
                print("⚠️", w)
                print("")

            try:
                tmp_arrow = pa.Table.from_pandas(mydf_fixed)
                pq.write_table(tmp_arrow, save_file)
                mysize = os.path.getsize(save_file)
                tmp_arrow = None
            except Exception as final_error:
                raise RuntimeError(
                    f"❌ Parquet save failed even after coercion: {final_error}"
                )

        return mysize

    def col_has_mixed_types(self, myseries, sample_size=100):
            try:
                sample = myseries.dropna().iloc[:sample_size]
                return len(sample.map(type).unique()) > 1
            except Exception:
                return True  # Fail-safe: assume mixed if error

    def coerce_mixed_columns(self, mydf, sample_size=100):
            df_fixed = mydf.copy()
            coercion_warnings = []
            for col in mydf.columns:
                if self.col_has_mixed_types(mydf[col], sample_size):
                    coercion_warnings.append(f"Column '{col}' had mixed types and was coerced to string.")
                    df_fixed[col] = mydf[col].astype(str)
            return df_fixed, coercion_warnings








    def loadPersistedDict(self):

        tstorloc = self.opts['persist_addon_dir'][0]
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
        self.persist_dir = tpdir

        self.persist_dict_pkl = self.persist_dir / "persist_dict.pkl"
        self.persisted_data_dir = self.persist_dir / "persisted_data"

        self.session_dict_pkl = self.persist_dir / "session_dict.pkl"
        self.session_data_dir = self.persist_dir / "session_data"

        self.checkDirs()

        if os.path.isfile(self.persist_dict_pkl):
            self.persist_dict_md5 = self.getPersistDictMD5()
            r = open(self.persist_dict_pkl, 'rb')
            self.persist_dict = pickle.load(r)
            r.close()
        else:
            self.persist_dict = {}

        if os.path.isfile(self.session_dict_pkl):
            self.session_dict_md5 = self.getPersistDictMD5()
            r = open(self.session_dict_pkl, 'rb')
            self.session_dict = pickle.load(r)
            r.close()
        else:
            self.session_dict = {}

        if self.debug:
            print(self.persist_dict)
            print(self.session_dict)

    def getnbname(self):
        if self.nbname is None:
            self.nbname = self.get_notebook_path()
        return self.nbname

    def listDataframes(self, inc_prev=True):
        our_dfs = {}
        for k, v in self.ipy.user_ns.items():
            if isinstance(v, pd.DataFrame):
                if inc_prev:
                    our_dfs[k] = v.shape
                else:
                    if k.find("prev_") != 0:
                        our_dfs[k] = v.shape
        return our_dfs

    def loadSession(self, line):
        byolo = False

        this_nb = self.getnbname()

        line = line.replace("session load", "")

        if line.find("-yolo") >= 0:
            byolo = True
            line = line.replace("-yolo", "")

        if this_nb is None:
            print("Cannot determine notebook name - Not Loading")
            return None

        nb_sessions = self.session_dict.get(this_nb, [])
        if len(nb_sessions) > 0:
            nb_sessions = sorted(nb_sessions, key=lambda x: x['saved_time'], reverse=True)
            if line.strip() == "":
                load_sess_id = nb_sessions[0]['sess_id']
                load_sess = nb_sessions[0]
                line = f"current for notebook ({load_sess_id})"
            else:
                load_sess_id = None
                for s in nb_sessions:
                    if s['sess_id'] == line.strip():
                        load_sess_id = s['sess_id']
                        load_sess = s

                if load_sess_id is None:
                    print(f"The session you tried to load {line.strip()} does not exist in sessions for {this_nb}")
                    return None
        else:
            print("No Sessions exist for this noteboook")
            return None


        out = ""
        out += "## Dataframe Load\n"
        out += "------------------\n"
        out += f"- Session Requested: {line.strip()}\n"
        out += f"- Yolo mode (Just load and clobber any existing dataframes with same name): {byolo}\n"
        out += f"- Date last saved: {load_sess['saved_time']}\n"
        out += f"- Total Size: {load_sess['total_space']}\n"
        out += f"- No. of Dataframes: {len(load_sess['saved_dfs'])}\n"
        out += "\n\n"
        out += "### Dataframes in Session\n"
        out += "--------------\n"
        out += "| Dataframe Name | Dataframe Name in Kernel |\n"
        out += "| -------------- | ------------------------ |\n"

        collision_potential = False
        for k, v in load_sess['saved_dfs'].items():
            k_in_ipy = k in self.ipy.user_ns
            if k_in_ipy:
                collision_potential = True
            out += f"| {k} | {k_in_ipy} |\n"
        out += "\n\n"

        if collision_potential:
            out += "**WARNING: There are names in the saved session already defined in kernel**\n"
            out += "**Answering Yes will overwrite current kernel variables with saved session variables**\n"
            out += "\n\n"

        jiu.displayMD(out)
        if not byolo:
            do_you_yolo = input("Do you wish to load the session listed above? Type Yes: ")
            if do_you_yolo.lower() == "yes":
                byolo = True
            else:
                print("Session Load canceled!")
                return None
        print("Loading Dataframes: ")
        for k, v in load_sess['saved_dfs'].items():
            this_df = self.loadPersistedDF(v, sessionid=load_sess_id)
            if this_df is None:
                this_df_shape = "Error Loading"
            else:
                this_df_shape = this_df.shape
                self.ipy.user_ns[k] = this_df
            print(f"\t{k} -> {this_df_shape}")




    def loadDF(self, line):
        tline = line.replace("load", "").strip()
        tar = tline.split(" ")
        myid = tar[0].replace("id:", "").strip()
        mydfstr = tar[1].strip()

        if self.debug:
            print("ID: %s" % myid)
            print("Var: %s" % mydfstr)

        if mydfstr in self.ipy.user_ns.keys() and self.ipy.user_ns[mydfstr] is not None:
            print("Cannot load dataframe as %s because that variable exists and is not None in the namespace, please pick another" % mydfstr)
        else:
            tdf = self.loadPersistedDF(myid)
            if tdf is not None:
                self.ipy.user_ns[mydfstr] = tdf

    #def lookupID(self, id):
    #    retval = id
    #    for x in self.persist_dict.keys():
    #        if x.find(id) == 0:
    #            retval = x
    #            break
    #    return retval



    def loadPersistedDF(self, myid, sessionid=None):
        # Updated for arrow
        mydf = None
        storage = self.retStorageMethod()

#        myid = self.lookupID(myid)
        if sessionid is None:
            # First check for the ID in the persist dict
            if myid not in self.persist_dict.keys():
                print("The id %s not found in currently persisted data" % myid)
                return None
            else:
                fname = myid + "." + storage
                load_fname = self.persisted_data_dir / fname
                if not os.path.isfile(load_fname): # Couldn't find store file
                    if storage == 'parq': # If its parq at least check for a pkl
                        fname = myid + ".pkl"
                        if os.path.isfile(self.persisted_data_dir / fname): # Well I guess that ID got stored wrong, so lets do pkl
                            storage = "pkl"
                            load_fname = self.persisted_data_dir /fname
                        else:
                            print("ID found but storage file not found in parq or pkl - Error")
                            return None
                    else: # if already pkl, we don't check for parq
                        print("ID found by storage file not found in pkl - Error")
                        return None
        else: # This is a Session Load
            fname = myid + "." + storage
            load_fname = self.session_data_dir / sessionid / fname
            if not os.path.isfile(load_fname): # Can't find the file
                if self.debug:
                    print(f"Cannot find id {myid} in {session_id} - Skipping")
                    return None

        if storage == "pkl":
            r = open(load_fname, 'rb')
            mydf = pickle.load(r)
            r.close()
        elif storage == "parq":
            tmp_arrow = pq.read_table(load_fname)
            mydf = tmp_arrow.to_pandas()
            tmp_arrow = None

        return mydf




    def saveSession(self, line):
        byolo = False
        boverwrite = True
        bincprev = False

        this_nb = self.getnbname()

        if line.find("-yolo") >= 0:
            byolo = True
            line = line.replace("-yolo", "")
        if line.find("-nooverwrite") >= 0:
            boverwrite = False
            line = line.replace("-nooverwrite", "")
        if line.find("-incprev") >= 0:
            bincprev = True
            line = line.replace("-incprev", "")

        cur_dataframes = self.listDataframes(inc_prev=bincprev)

        out = ""
        out += "## Dataframe Session Save\n"
        out += "-----------\n"
        out += f" - Overwrite Current: {boverwrite} (-nooverwrite to save a new session for notebook)\n"
        out += f" - Include dataframes starting with prev_: {bincprev} (-incprev to include dataframes starting with prev_)\n"
        out += f" - Yolo Mode (just save, no confirmation): {byolo} (-yolo if you only live once)\n"
        out += "\n\n"
        out += "### Dataframes in Sessions\n"
        out += "-------------------\n"
        out += "| Dataframe Name | Dataframe Shape |\n"
        out += "| -------------- | --------------- |\n"
        for k, v in cur_dataframes.items():
            out += f"| {k} | {v} |\n"
        out += "\n\n"

        jiu.displayMD(out)
        if not byolo:
            do_you_yolo = input("Do you wish to save the session with the information above? Type Yes: ")
            if do_you_yolo.lower() == "yes":
                byolo = True
            else:
                print("Session Save canceled!")
                return None

        nb_sessions = self.session_dict.get(this_nb, [])
        cur_sess = None
        if len(nb_sessions) > 0:
            nb_sessions = sorted(nb_sessions, key=lambda x: x['saved_time'], reverse=True)
            if boverwrite:
                cur_sess = nb_sessions[0]['sess_id']

        if boverwrite and cur_sess is not None:
            pass
        else:
            cur_sess = self.getUUID()
        save_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        save_rec = {"sess_id": cur_sess, "saved_time": save_time}

        new_session_dir = self.session_data_dir / cur_sess

        b_saved = False
        if os.path.isdir(new_session_dir):
            if not boverwrite:
                print(f"Directory for session {cur_sess} found at {session_dir} and boverwrite is {boverwrite}. Exiting")
                return None
            cur_session_dir = self.session_data_dir / f"old_{cur_sess}"
            os.rename(new_session_dir, cur_session_dir)
            b_saved = True

        try:
            os.makedirs(new_session_dir)

            sess_size = 0
            saved_dfs = {}
            for k, v in cur_dataframes.items():
                this_id = self.getUUID()
                this_df = self.ipy.user_ns[k]
                if isinstance(this_df, pd.DataFrame):
                    print(f"Saving: {k}")
                    this_size = self.saveData(this_id, this_df, sessionid=cur_sess)
                    sess_size += this_size
                    saved_dfs[k] = this_id
                else:
                    print(f"Skipping {k} as it's  not a Dataframe somehow")
            save_rec['saved_dfs'] = saved_dfs
            save_rec['total_space'] = sess_size
            if self.debug:
                print("Current Sessions")
                print(nb_sessions)
                print(f"New sessions {save_rec}")
            new_nb_sessions = []
            new_nb_sessions.append(save_rec)
            if len(nb_sessions) > 0:
                for s in nb_sessions:
                    if s['sess_id'] == cur_sess:
                        pass
                    else:
                        new_nb_sessions.append(s)

            self.session_dict[this_nb] = new_nb_sessions
            self.saveSessionsDict()

        except Exception as e:
            print(f"Error Saving Session for {this_nb} - {e}")
            if b_saved:
                print(f"Due to Error, putting old session save info back")
                shutil.rmtree(new_session_dir)
                os.rename(cur_session_dir, new_session_dir)
            return None
        if b_saved:
            if self.debug:
                print("Deleting Saved Data")
            shutil.rmtree(cur_session_dir)
        print("")
        print(f"Sessions for {this_nb} saved as ID: {cur_sess}")


    def saveSessionsDict(self):
        # Ok for Arrow
        f = open(self.session_dict_pkl, 'wb')
        # TODO Handle Merges
        pickle.dump(self.session_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.close()


    def saveData(self, myid, mydf, sessionid=None):
        # Updated for Arrow
        storage = self.retStorageMethod()
        fname = myid + "." + storage


        if sessionid is None:
            sfile = self.persisted_data_dir / fname
        else:
            sfile = self.session_data_dir / sessionid / fname

        if storage == 'pkl':
            f = open(sfile, 'wb')
            pickle.dump(mydf, f, protocol=pickle.HIGHEST_PROTOCOL)
            f.close()
            mysize = os.path.getsize(sfile)
        elif storage == 'parq':
            if self.debug:
                print(f"File: {sfile}")
            mysize = self.saveParquetFile(mydf, sfile)
#            tmp_arrow = pa.Table.from_pandas(mydf)
#            pq.write_table(tmp_arrow, sfile)
#            mysize = os.path.getsize(sfile)
#            tmp_arrow = None
        else:
            print("Unknown storage: %s" % storage)
            mysize = 0

        return mysize



    def listSessions(self, line):

        nb_test = line.replace("session list", "").strip()
        if nb_test == "":
            this_nb = self.getnbname()
        else:
            this_nb = nb_test

        if this_nb is None:
            return f"**Can't determine notebook name - No Sessions to list**"

        nbs_dict = {}
        if self.debug:
            print(f"List Sessions NB Name: {this_nb}")
        if this_nb != 'all':
            sessions = self.session_dict.get(this_nb, None)
            if sessions is None:
                return f"**No sessions for notebook {this_nb} found**"
            else:
                nbs_dict = {this_nb: sessions}
        else:
            nbs_dict = self.session_dict.copy()


        out = ""
        if this_nb == 'all':
            if self.debug:
                print("In print block for All sessions")
            out += f"## All Notebooks and Sessions\n\n"

        for k, v in nbs_dict.items():
            cur_nb_name = k
            these_sessions = sorted(v, key=lambda x: x['saved_time'], reverse=True)

            this_total_size = sum(item['total_space'] for item in these_sessions)


            out += f"### Sessions for {k}\n"
            out += f"**Total Size: {this_total_size/1000:,}MB**\n"
            out += "------------------------\n"
            out += "| Session Id | Saved TS | No. of DFs | Total Space (MB) |\n"
            out += "| ---------- | -------  | ---------- | ---------------- |\n"
            for s in these_sessions:
                out += f"| {s['sess_id']} | {s['saved_time']} | {len(s['saved_dfs'])} | {s['total_space']/1000:,} |\n"
            out += "\n\n"

        return out
    def deleteSession(self, line):
        byolo = False

        orig_line = line

        line = line.replace("session delete", "")

        if line.find("-yolo") >= 0:
            byolo = True
            line = line.replace("-yolo", "")

        pattern = r'(^|\s)([0-9a-f]{32})(\s|$)'

        matches = re.findall(pattern, line)
        del_sessions = [m[1] for m in matches]
        del_sessions = [x.strip() for x in del_sessions]
        for s in del_sessions:
            line = line.replace(s, "")
        line = line.strip()
        if line == "":
            this_nb = self.getnbname()
        elif line.find(".ipynb") > 0:
            this_nb = line
        else:
            print("Unknown line, is not a session ID, or an ipynb - Not deleting")
            print(f"Original line: {orig_line}")
            print(f"Processed line: {line}")
            return None


 #       if len(del_sessions) < 1:
 #           print("No sessions found")

        if this_nb is None:
            print("Cannot determine notebook name - Not Loading")
            return None

        nb_sessions = self.session_dict.get(this_nb, [])
        if len(nb_sessions) > 0:
            nb_sessions = sorted(nb_sessions, key=lambda x: x['saved_time'], reverse=True)
            if len(del_sessions) < 1:
                del_sess_id = nb_sessions[0]['sess_id']
                final_del_sess_ids = [del_sess_id]
                del_sess = [nb_sessions[0]]
                keep_sess = [x for x in nb_sessions if x['sess_id'] not in final_del_sess_ids]
                prov_sess = f"current for notebook ({del_sess_id})"
            else:
                all_sess_ids = [x['sess_id'] for x in nb_sessions]
                prov_sess = f"Prov Session: {del_sessions}"
                final_del_sess_ids = [x for x in del_sessions if x in all_sess_ids]
                del_sess = [x for x in nb_sessions if x['sess_id'] in final_del_sess_ids]
                keep_sess = [x for x in nb_sessions if x['sess_id'] not in final_del_sess_ids]
                if len(final_del_sess_ids) == 0:
                    print(f"No sessions to delete")
                    return None
        else:
            print(f"No Sessions exist for notebook {this_nb}")
            return None

        out = ""

        out += "## Dataframe Session Delete\n"
        out += "-----------\n"
        out += f" - Notebook for Session Deletion: {this_nb}\n"
        out += f" - Sessions for deletion: {prov_sess}\n"
        out += f" - Final session list: {final_del_sess_ids}\n"
        out += f" - Yolo Mode (just save, no confirmation): {byolo} (-yolo if you only live once)\n"
        out += "\n\n"
        out += "### Sessions for Deletion\n"
        out += "-------------------\n"
        out += "| Session ID | Saved | Total Size | No. of Dataframes |\n"
        out += "| ---------- | ----- | ---------- | ----------------- |\n"
        for x in del_sess:
            out += f"| {x['sess_id']} | {x['saved_time']} | {x['total_space']} | {len(x['saved_dfs'])} |\n"
        out += "\n\n"

        jiu.displayMD(out)
        if not byolo:
            do_you_yolo = input("Do you wish to delete the sessions with the information above? Type Yes: ")
            if do_you_yolo.lower() == "yes":
                byolo = True
            else:
                print("Session Delete canceled!")
                return None

        for s in del_sess:
            this_id = s['sess_id']
            sess_dir = self.session_data_dir /this_id
            shutil.rmtree(sess_dir)
        if len(keep_sess) > 0:
            self.session_dict[this_nb] = keep_sess
        else:
            del self.session_dict[this_nb]
        self.saveSessionsDict()


    def deletePersisted(self, line):
        # Updated for arrow
        bConf = False
        tid = line.replace("delete", "").strip()
        tidar = tid.split(" ")
        myid = tidar[0].replace("id:", "").strip()

        if len(tidar) > 1:
            conf = tidar[1].strip()
            if conf == "-conf":
                bConf = True

        #myid = self.lookupID(myid)
        if myid not in self.persist_dict.keys():
            print("ID %s does not found in persisted data. Please review %persist list for currrently known persisted data")
        else:
            if not bConf:
                dval = input("Please type the word 'delete' to remove persisted data with ID %s: " % myid)
                if dval.lower().strip() == "delete":
                    bConf = True
            if bConf:
                del_result = self.deleteID(myid)
            else:
                print("Persisted Data removal canceled by not typing delete")

    def deleteID(self, myid):

        storage = self.retStorageMethod()
        fname =  myid + "." + storage
        if not os.path.isfile(self.persisted_data_dir / fname):
            if storage == 'parq':
                fname = myid + ".pkl"
                if os.path.isfile(self.persisted_data_dir / fname):
                    storage = "pkl"
                else:
                    print("ID found but storage file not found in parq or pkl - Error")
                    return False
            else:
                print("ID found by storage file not found in pkl - Error")
                return False
        os.remove(self.persisted_data_dir / fname)
        del self.persist_dict[myid]
        self.savePersisted()
        print("Deleted Persisted data with ID %s" % myid)
        return True



    def purgePersist(self, line):
        bConf = False
        if line.find("-conf") >= 0:
            bConf = True
        if not bConf:
            dval = input("Please type the word 'purge' to confirm purging of all old persisted queries: ")
            if dval.lower().strip() == "purge":
                bConf = True
        if bConf:
            print("This is where we would purge by date! (TODO: Actually Purge stuff)")
        else:
            print("The Purge is canceled")

    def persistDF(self, myline, mycell):
        myid = ""
        mystrdf = ""
        mynotes = ""
        bConf = False

        tline = myline.replace("save", '').strip()
        tar = tline.split(" ")
        mystrdf = tar[0]
        tline = tline.replace(mystrdf, '').strip()
        tar = tline.split(" ")
        if tar[0].find("id:") == 0:
            # This is an ID
            myid = tar[0].replace("id:", '').strip()
            tline = tline.replace(tar[0], '').strip()
        mynotes = mycell.strip()
        if tline.find("-conf") >= 0:
            bConf = True
        if self.debug:
            print("Saving Df: %s" % mystrdf)
            print("Id: %s" % myid)
            print("Notes: %s" % mynotes)
            print("bConf: %s" % bConf)
        if mystrdf in self.ipy.user_ns:
            mydf = self.ipy.user_ns[mystrdf]
        else:
            print("%s variable not found in user namespace, not persisting" % mystrdf)
            return None

        if isinstance(mydf, pd.DataFrame):
            newid = self.persistData(mydf, notes=mynotes, id=myid, confirm=bConf)
            print("Dataframe %s persisted with ID %s" % (mystrdf, newid))
        else:
            print("The variable %s, while it exists, is NOT a dataframe, therefore we will not persist it" % mystrdf)



    def persistData(self, thedata, notes="", integration="", instance="", query="", id="", confirm=False):
        bConf = confirm
        savetime = int(time.time())

        if id != "":
            #id = self.lookupID(self.lookupid(id))
            if id in self.persist_dict.keys():
                if not bConf:
                    dval = input("ID %s already exists, please type confirm to confirm overwriting results: " % id)
                    if dval.lower().strip() == "confirm":
                        bConf = True
            else:
                print("id does not exist, and we don't allow custom id - your ID will be ignored")
                id = ""
                cConf = True
        else:
            bConf = True
        if id == "":
            id = self.getUUID()

        if isinstance(thedata, pd.DataFrame):
            if bConf:
                  # {"a88167960e644cceb6dfd1531ef2cde0": {"qtime": 1611754956, "pkl_size": 13321, "integration": "Splunk", "instance": "testing", "query": "search myterm='ff', 'notes':'some notes'} # file name is a88167960e644cceb6dfd1531ef2cde>
                mysize = self.saveData(id, thedata)
                myrec = {"qtime": savetime, "pkl_size": mysize, "integration": integration, "instance": instance, "query": query, "notes": notes}
                self.loadPersistedDict()
                self.persist_dict[id] = myrec
                self.savePersisted()
                return id
            else:
                print("We are not going on due to duplicate ids")
        else:
            print("You tried to save a non dataframe, we only allow saving of dataframes")
        return None




    def getUUID(self):
        return uuid.uuid4().hex

    def customHelp(self, curout):
        n = self.magic_name
        m = "%" + n
        mq = "%" + m

        table_header = "| Magic | Description |\n"
        table_header += "| -------- | ----- |\n"

        out = curout

        out += "\n"
        out += "### %s management line magics\n" % (m)
        out += "---------------\n"
        out += table_header
        out += "| %s | Refresh the list of persisted data (helpful if you saved on a different notebook) |\n" % (m + " refresh")
        out += "| %s | List currently persisted data |\n" % (m + " list")
        out += "| %s | Delete a specifc persist 'id' use -conf to force no confirmation |\n" % (m + " delete 'id' [-conf]")
        out += "| %s | Purge all persisted data older than persist_purge_days. Add -conf to do so without confirmation |\n" % (m + " purge [-conf]")
        out += "| %s | List all Dataframes (and shapes) that exist in the current kernel |\n" % (m + " listdfs")
        out += "\n\n"

        out += "### %s Dataframe Saving\n" % (mq)
        out += "---------------\n"
        out += table_header
        out += "| %s | Save Dataframe 'df' add -conf to auto overwrite with 'notes' on the dataframe |\n" % (mq + " save 'df' [-conf]<br>'notes'")
        out += "| %s | Save Dataframe mydf with the notes 'Dataframe saved due to amazing findings' |\n" % (mq + " save mydf<br>Dataframe saved due to amazing findings")
        out += "\n\n"

        out += "### %s Dataframe Loading\n" % (m)
        out += "---------------\n"
        out += table_header
        out += "| %s | Load persisted data with id 'id' into 'newvar' |\n" % (m + " load 'id' 'newvar'")
        out += "| %s | Load id 8123ab into variable saved_df |\n" % (m + " load 8123ab saved_df")
        out += "\n\n"

        out += "### %s Shared Datasets\n" % (m)
        out += "---------------\n"
        out += table_header
        out += "| %s | Save Dataframe 'df' to shared location and get a id to share  |\n" % (m + " shared save df")
        out += "| %s | Load Saved id into df |\n" % (m + " shared load id df")
        out += "\n\n"

        out += "### %s Session Datasets\n" % (m)
        out += "---------------\n"
        out += table_header
        out += "| %s | Save a session (current Notebook)  |\n" % (m + " session save")
        out += "| %s | Load a session (current Notebook)  |\n" % (m + " session load")
        out += "| %s | Delete a session (current or Other Notebook)  |\n" % (m + " session delete")
        out += "| %s | List Sessions (current Notebook add 'all' to see all sessions)  |\n" % (m + " session list")
        out += "\n\n"


        return out

    def retCustomDesc(self):
        return __desc__

    def customStatus(self):
        # Todo put in information about the persisted information
        out = ""
        out += "\n"
        out += "### Current Persistance Information\n"
        out += "-----\n"
        out += "Number of Persisted Data Items: %s\n" % len(self.persist_dict.keys())
        out += "\n"
        return out



    def get_notebook_path(self):
        conn_file = self.ipy.config['IPKernelApp']['connection_file']
        kernel_id = os.path.basename(conn_file).split('-', 1)[1].split('.')[0]

        if self.debug:
            print(f"Conn File: {conn_file}")
        for server in serverapp.list_running_servers():
            try:
                response = requests.get(url=f"{server['url']}api/sessions", params={'token': server.get('token', '')})
                sessions = response.json()
                for sess in sessions:
                    if self.debug:
                        print(type(sess))
                    if isinstance(sess, str):
                        continue
                    if sess['kernel']['id'] == kernel_id:
                        return sess['notebook']['path']
            except Exception as e:
                print(f"Error querying {server['url']} with {server.get('token', '')}: {e}")
        return None




    def printDFs(self):
        our_dfs = self.listDataframes()
        our_nbname = self.get_notebook_path()
        out = ""
        out += f"# Dataframes in {our_nbname}\n"
        out += "----------------\n"
        out += "| Dataframe Name | Dataframe Shape |\n"
        out += "| -------------- | --------------- |\n"
        for k, v in our_dfs.items():
            out += f"| {k} | {v} |\n"
        out += "\n\n"
        return out


    # This is the magic name.
    @line_cell_magic
    def persist(self, line, cell=None):
        line = line.replace("\r", "")
        if cell is None:
            line_handled = self.handleLine(line)
            if self.debug:
                print("line: %s" % line)
                print("cell: %s" % cell)
            if not line_handled: # We based on this we can do custom things for integrations. 
                if line.lower().strip() == "list":
                    jiu.displayMD(self.retPersisted())
                elif line.lower().strip().find("refresh") == 0:
                    self.loadPersistedDict()
                    if line.lower().strip().replace("refresh", "").strip() == "":
                        jiu.displayMD(self.retPersisted())
                elif line.lower().find("delete") == 0:
                    self.deletePersisted(line)
                elif line.lower().find("session list") == 0:
                    jiu.displayMD(self.listSessions(line))
                elif line.lower().find("session save") == 0:
                    self.saveSession(line)
                elif line.lower().find("session load") == 0:
                    self.loadSession(line)
                elif line.lower().find("session delete") == 0:
                    self.deleteSession(line)
                elif line.lower().find("purge") == 0:
                    self.purgePersist(line)
                elif line.lower().find("save") == 0:
                    self.persistDF(line)
                elif line.lower().find("load") == 0:
                    self.loadDF(line)
                elif line.lower().find("shared") == 0:
                    self.procShared(line)
                elif line.lower().find("listdfs") == 0:
                    jiu.displayMD(self.printDFs())
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            if line.lower().find("save") == 0:
                self.persistDF(line, cell)

