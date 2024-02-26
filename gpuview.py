# -*- coding: utf-8 -*-
import typing
from   typing import *

min_py = (3, 11)

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

DAT_FILE=os.path.join(os.getcwd(), 'info_gpu.dat')
padding = lambda x: " "*x


### cleaned up
#nvidia-smi --query-gpu=index,pstate,power.draw,temperature.gpu,fan.speed,memory.used,memory.total,utilization.gpu --format=csv,noheader

columns = ["host", "gpu_id", "pstate", "powerdraw", "temperature", "fanspeed", "memused", "memtotal", "util"]
values = []
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
    db.execute_SQL(gpu_create) #create table if does not exist
    return

@trap
def get_list_GPU_ws():
    """
    Return list of workstations with GPU/GPUs.
    """
    with open(myargs.input, "rb") as f:
        contents = tomllib.load(f)
    try:
        result = contents["ws"]["gpu"]
    except:
        result = None
    return result

@trap
def record_info(ws:str, info):
    """
    Insert GPU metrics into the database. 
    """
    create_gpu_table()
    for dict in info:
        tuple_to_insert = tuple(dict.values())
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
                     VALUES {tuple_to_insert}"""
        db.execute_SQL(sql_insert)
    return

@trap
def prepare_data(ws:str):
    """
    Convert GPU memory and utilization to ratios and create graphs
    in the following form
    host, id, pstate, power, temp, fan, [MMMM___________] [UUUUUUUU_________]
    """
    info = nvidia_smi(ws).split("\n")
    data_for_db = []
    data_for_display = []
    color = "" #identify a color of the graph
    #iterate over several GPUs information and create a list of dictionaries
    for idx, gpu in enumerate(info):
        values = []
        values.append(ws)
        for metric in info[idx].split(","):
            values.append(metric.strip())
        # create a dictionary for easier access 
        dict_info = {k:v for (k,v) in zip(columns, values)}
        
        #if multiple GPUs, append all dicts to a list
        data_for_db.append(dict_info)

        powerdraw = dict_info["powerdraw"].split()[0]
        fanspeed = dict_info["fanspeed"].split()[0]
        memused = dict_info["memused"].split(" ")[0]
        memtotal = dict_info["memtotal"].split(" ")[0] 
        graph_mem = row(int(memused), int(memtotal), "M")

        util = dict_info["util"].split(" ")[0]
        graph_util = row(int(util), 100, "U") #util is measure in %, so 100 is max 
        
        if anomaly(dict_info["temperature"], memused, memtotal):
            color = "⚠️"
        elif warning(dict_info["temperature"], memused, memtotal):
            color = "🛑"
        else:
            color = "✅"       
        data_for_display.append(["("+dict_info["gpu_id"]+")"+f"{''.ljust(3)}", #+padding(col_width)+str(col_width), 
                                dict_info["pstate"].ljust(5), 
                                powerdraw.ljust(8), 
                                dict_info["temperature"].ljust(5), 
                                fanspeed.ljust(5), 
                                graph_mem.ljust(5), graph_util, color])


    #insert numerical entries into the database
    record_info(ws, data_for_db)
     
    return data_for_display 

@trap
def fork_ssh() -> None:
    '''
    Multiprocesses to ssh to each workstation and retrieve information
    in parallel, significantly speeding up the process.
    '''
    global DAT_FILE, logger

    try:
        ws_lst = get_list_GPU_ws()
    except:
        logger.info(piddly("Nothing to do for no workstation."))


    try:
        os.unlink(DAT_FILE)
    except FileNotFoundError as e:
        # This is OK; the file has already been deleted.
        pass

    except Exception as e:
        # This is something else, let's find out what happened.
        logger.error(piddly(f"Cannot continue. Unable to clear {DAT_FILE} because {e}."))
        sys.exit(os.EX_IOERR)

    pids = set()

    for ws in ws_lst:

        # Parent process records the child's PID.
        if (pid := os.fork()):
            pids.add(pid)
            continue

        with open(DAT_FILE, 'a+') as infodat_gpu:
            try:
                data = prepare_data(ws)
                # each child process locks, writes to and unlocks the file
                fcntl.lockf(infodat_gpu, fcntl.LOCK_EX)
                for idx, gpu_data in enumerate(data):
                    infodat_gpu.write(f'{ws.ljust(7)} {" ".join(data[idx])}\n')
                infodat_gpu.close()

            except Exception as e:
                logger.error(piddly(f"query of {ws} failed. {e}"))
                pass

            finally:
                for gpu_data in data:
                    logger.info(piddly(f"{ws} {gpu_data}"))
                os._exit(os.EX_OK)

    # make sure all the child processes finished before the function
    # returns.
    while pids:
        # The zero in the argument means we wait for any child.
        # The resulting pid is the child that sent us a SIGCHLD.
        pid, exit_code, _ = os.wait3(0)
        pids.remove(pid)

@trap 
def warning(temp, memused, memtotal) -> bool:
    """
    Return true if GPU's metrics need attention.
    True if temperature > 55C, used memory > 50%.
    """
    mem_ratio = (int(memused) * 100) / int(memtotal)
    if int(temp) >=55 or mem_ratio > 50:
        return True
    else:
        return False

@trap 
def anomaly(temp, memused, memtotal) -> bool:
    """
    Return True if GPU metrics signal of anomaly.
    True, if temperature > 65C, used memory > 80%.
    """
    mem_ratio = (int(memused) * 100) / int(memtotal)
    if int(temp) >=65 or mem_ratio > 80:
        return True
    else:
        return False

@trap
def display_data(stdscr: object):
    """
    Use ncurses to draw the graphs in the terminal window.
    The window is interactive and can be refreshed.
    """

    # initialize the color, use ID to refer to it later in the code
    # params: ID, font color, background color
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

    #use the color, uses a variable assignment
    GREEN_AND_BLACK = curses.color_pair(1)
    YELLOW_AND_BLACK = curses.color_pair(2)
    WHITE_AND_BLACK = curses.color_pair(3)
    RED_AND_BLACK = curses.color_pair(4)

    stdscr.clear()
    stdscr.nodelay(1)

    # resize window if needed
    height,width = stdscr.getmaxyx()
    logger.info(piddly(f"Initialized a screen, {height}x{width}"))

    window2 = curses.newwin(0,0, 1,1)
    help_win = curses.newwin(0,0, 1,1)

    window2.bkgd(' ', WHITE_AND_BLACK)
    help_win.bkgd(' ', WHITE_AND_BLACK)

    left_panel = curses.panel.new_panel(window2)
    help_panel = curses.panel.new_panel(help_win)
    help_panel.hide()

    curses.panel.update_panels()
    curses.doupdate()

    running = True
    help_win_up = False
    x = 0

    while ( running ):
        #display the CPU and memory availability graph for each workstation
        try:
            # window with help message
            if help_win_up:
                window2.clear()
                window2.refresh()
                left_panel.hide()
                help_panel.show()

                help_win.addstr(0, 0, gpu_header(), WHITE_AND_BLACK)
                help_win.addstr(2, 0, example_map_gpu()[0], YELLOW_AND_BLACK)
                help_win.addstr(3, 0, example_map_gpu()[1], GREEN_AND_BLACK)
                help_win.addstr(4, 0, help_msg_gpu(), WHITE_AND_BLACK)

                help_win.addstr(15, 0, "Press b to return to the main screen.")
                help_win.refresh()
                ch = help_win.getch()
                if ch == curses.KEY_RESIZE:
                    height,width = stdscr.getmaxyx()
                    help_win.resize(height, width)
                    help_panel.replace(help_win)
                    help_panel.move(0,0)
                    help_panel.show()
                if ch == ord('b'):
                    help_win_up = False
                    help_panel.hide()
                    help_win.clear()
                    continue

            # map the main window with CPU usage map and memory usage information.
            else:
                window2.addstr(0, 0, header_gpu(), WHITE_AND_BLACK)
                with open(DAT_FILE) as infodat:
                    info = infodat.readlines()
                    for idx, graph in enumerate(sorted(info)):
                        if "🛑" in graph: 
                            window2.addstr(idx+2, 0, graph, RED_AND_BLACK)
                        elif "⚠️" in graph:
                            window2.addstr(idx+2, 0, graph, YELLOW_AND_BLACK)
                        elif "✅" in graph:
                            window2.addstr(idx+2, 0, graph, GREEN_AND_BLACK)
                        else:
                            window2.addstr(idx+2, 0, graph, WHITE_AND_BLACK)
                window2.addstr(len(info)+3, 0, f'Last updated {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}', WHITE_AND_BLACK)
                window2.addstr(len(info)+4, 0, "Press q to quit, h for help OR any other key to refresh.", WHITE_AND_BLACK)

                window2.refresh()
        except:
            pass

        #work around window resize
        window2.timeout(myargs.refresh*1000)
        k = window2.getch()
        if k == -1:
            pass
        elif k == curses.KEY_RESIZE:
            height,width = stdscr.getmaxyx()
            window2.resize(height, width)
            left_panel.replace(window2)
            left_panel.move(0,0)
        elif k == ord('q'):
            running = False
            curses.endwin()

        # help message panel
        elif k == ord('h'):
            help_win_up = True

        curses.panel.update_panels()
        curses.doupdate()
        stdscr.refresh()
        window2.refresh()
    pass

@trap
def gpuview_main(myargs:argparse.Namespace) -> int:
    fork_ssh()
    wrapper(display_data)
    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="gpuview", 
        description="What gpuview does, gpuview does best.")

    parser.add_argument('-i', '--input', type=str, default="wscontrol.toml",
        help="If present, --input is interpreted to be a whitespace delimited file of host names.")    
    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    parser.add_argument('-v', '--verbose', action='store_true',
        help="Be chatty about what is taking place")
    parser.add_argument('--sql', default = "wscontrol.sql",
        help="SQL statements of the project.")
    parser.add_argument('--db', type=str, default="wscontrol.db",
        help="The program will insert data into the database.") 
    parser.add_argument('-r', '--refresh', type=int, default=60,
        help="Refresh interval defaults to 60 seconds. Set to 0 to only run once.")

    myargs = parser.parse_args()
    verbose = myargs.verbose
    logger = wsview_utils.URLogger(level=myargs.verbose)
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

