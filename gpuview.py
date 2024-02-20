# -*- coding: utf-8 -*-
import typing
from   typing import *

min_py = (3, 8)

###
# Standard imports, starting with os and sys
###
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
import contextlib
import getpass
mynetid = getpass.getuser()
import curses
import curses.panel
from   curses import wrapper
from   datetime import datetime
import fcntl
import logging
import re
import shutil
import sqlite3
import time
import tomllib
import math
mynetid = getpass.getuser()

###
# imports and objects that are a part of this project
###
from   wrapper import trap
from dorunrun import dorunrun
import sqlitedb
from sqlitedb import SQLiteDB
import wsview_utils
from wsview_utils import * 

###
# From hpclib
###
import linuxutils
from   urdecorators import trap

###
# imports and objects that are a part of this project
###
verbose = False

###
# Credits
###
__author__ = 'Alina Enikeeva'
__copyright__ = 'Copyright 2024, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'Alina Enikeeva'
__email__ = 'alina.enikeeva@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'

DAT_FILE=os.path.join(os.getcwd(), 'info.dat')
padding = lambda x: " "*x


### cleaned up
#nvidia-smi --query-gpu=index,pstate,power.draw,temperature.gpu,fan.speed,memory.used,memory.total,utilization.gpu --format=csv,noheader

@trap
def nvidia_smi(ws:str):
    """
    Run nvidia-smi to get the metrics we need.
    """
    cmd = f"ssh -o ConnectTimeout=5 {ws} nvidia-smi --query-gpu=index,pstate,power.draw,temperature.gpu,fan.speed,memory.used,memory.total,utilization.gpu --format=csv,noheader"

    result = dorunrun(cmd, return_datatype=dict)

    return result['stdout']

@trap
def create_gpu_table():
    """
    Create gpu table if it doesn't exist.
    """
    gpu_create = """CREATE TABLE IF NOT EXISTS gpu (
        t datetime default current_timestamp,
        host varchar(20),
        gpu_id varchar(20),
        pstate varchar(20),
        powerdraw varchar(20),
        temperature varchar(20),
        fanspeed varchar(20),
        memused varchar(20),
        memtotal varchar(20),
        util varchar(20)
        )
        """
    print(gpu_create)
    
    db.execute_SQL(gpu_create) #create table if does not exist
    return

@trap
def get_memory(ws:str, info) -> dict:
    """
    Collects and returns used and total memory for the workstation's GPU.
    """
    d = {}
    return d

@trap
def get_fanspeed(ws:str) -> dict:
    """
    Collects and returns the fan speed of GPU.
    """
    d = {}

    return d

@trap 
def get_power(ws:str) -> dict:
    """
    Collects and returns the power drawn by GPU.
    """
    return

@trap 
def get_temp(ws:str) -> dict:
    """
    Collects and returns temperature of GPU.
    """
    return

@trap
def get_util(ws:str) -> dict:
    """
    Collects and returns GPU-Util (utilization) metric.
    """
    return

@trap
def get_list_GPU_ws():
    """
    Return list of workstations with GPU/GPUs.
    """
    with open(myargs.input, "rb") as f:
        contents = tomllib.load(f)
    try:
        result = contents["ws"]["GPU"]
    except:
        result = None
    return result

@trap
def record_info(ws:str, info):
    """
    Insert GPU metrics into the database. 
    """
    create_gpu_table()
    sql_insert = f"""INSERT INTO gpu 
                        (host, 
                        gpu_id, 
                        pstate, 
                        powerdraw, 
                        temperature, 
                        fanspeed, 
                        memused, 
                        memtotal, 
                        util) 
                     VALUES (?,?,?,?,?,?,?,?,?)"""
    
    db.execute_SQL(sql_insert,info)

@trap
def prepare_data(ws:str):
    """
    Convert GPU memory and utilization to ratios and create graphs
    in the following form
    host, id, pstate, power, temp, fan, [MMMM___________] [UUUUUUUU_________]
    """
    info = nvidia_smi(ws)   
    
    #make a dictionary 
    dict_info = info #do dictionary comprehension!!!!
    
 
    #insert numerical entries into the database
    record_info(ws, info)
    
    r_c = ""
    r_m = ""
    warning = ""

    #prepare the graphs
    if "n/a" in cpu.values(): 
        r_c = "No CPU information." +padding(23)
    else:
        r_c = row(cpu["used"], cpu["total"], "C")

    if "n/a" in mem.values():
        r_m = "No memory information."
    else:
        r_m = row(mem["used"], mem["total"], "M")

    if cpu["how_busy"] > 0.75 or mem["how_busy"] > 0.75:
        warning = "Almost Full"
    

    return " ".join((r_c, r_m, warning))

@trap
def gpuview_main(myargs:argparse.Namespace) -> int:
    print(nvidia_smi("irene"))
    record_info("irene", nvidia_smi("irene"))
    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="gpuview", 
        description="What gpuview does, gpuview does best.")

    parser.add_argument('-i', '--input', type=str, default="",
        help="Input file name.")
    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    parser.add_argument('-v', '--verbose', action='store_true',
        help="Be chatty about what is taking place")
    parser.add_argument('--sql', default = "wscontrol.sql",
        help="SQL statements of the project.")
    parser.add_argument('--db', type=str, default="wscontrol.db",
        help="The program will insert data into the database.") 

    myargs = parser.parse_args()
    verbose = myargs.verbose

    try:
        db = sqlitedb.SQLiteDB(myargs.db)
    except:
        db = None
        print(f"Unable to open {myargs.db}")
        sys.exit(EX_CONFIG)

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

