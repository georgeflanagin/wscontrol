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
import curses
import curses.panel
from   curses import wrapper
from   datetime import datetime
import getpass
import fcntl
import logging
import re
import shutil
import sqlite3
import time
import toml
import math
mynetid = getpass.getuser()

#import view_utils
#from view_utils import *
from   wrapper import trap
from dorunrun import dorunrun
import sqlitedb
from sqlitedb import SQLiteDB
import wsview_utils
from wsview_utils import * 
###
# imports and objects that are a part of this project
###
verbose = False

###
# Credits
###
__author__ = 'Alina Enikeeva'
__copyright__ = 'Copyright 2023, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'Alina Enikeeva, George Flanagin'
__email__ = 'hpc@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'

DAT_FILE=os.path.join(os.getcwd(), 'info.dat')

@trap
def get_memory(ws:str) -> dict:
    """
    Collects and returns used and total  memory for the workstation
    """
    d = {}

    try:
        cmd = f"ssh -o ConnectTimeout=1 {ws} free"
        result = dorunrun(cmd, return_datatype = str)
        used = float(result.split()[8])
        total = float(result.split()[7])

        d["used"] = used
        d["used_ratio"] = used * 100 / total
        d["total"] = total
   
    except:
        d["used"] = "n/a"
        d["total"] = "n/a"

    return d

@trap
def get_cpu(ws:str) -> dict:
    """
    Collects and returns used and total CPUs from the worsktation.
    """
    d = {}

    try:
        cmd_total = f"ssh -o ConnectTimeout=1 {ws} nproc"
        cmd_used = f"ssh -o ConnectTimeout=1 {ws} w"
        total = float(dorunrun(cmd_total, return_datatype = str))
        used = dorunrun(cmd_used, return_datatype=str).split()[9]
        used = float(used.split(",")[0])
        d["used"] = used
        d["used_ratio"] = used*100 / total  #calculate ration of used cpu
        d["total"] = total
    except:
        d["used"] = "n/a"
        d["total"] = "n/a"
    return d

@trap
def get_list_of_ws(lst:str):
    """
    Return list of workstations based on who they belong to.
    """
    with open(myargs.input, "r") as f:
        contents = toml.load(f)
    result = contents["ws"][lst]
    return result

@trap
def record_info(ws:str, cpu:dict, mem:dict):
    """
    Insert CPU and memory usage to the database. 
    """
    sql_insert = f"""INSERT INTO cpu_mem (host, cpu_used, cpu_total, mem_used, mem_total) VALUES (?,?,?,?,?)"""
    db.execute_SQL(sql_insert, ws, cpu["used"], cpu["total"], mem["used"], mem["total"])

@trap
def prepare_data(ws:str):
    """
    Convert cpu and memory usage to ratios and create graphs
    in the following form
    host [CCCC_____________] [MMMMMMMMM_________]
    """
    mem = get_memory(ws)
    cpu = get_cpu(ws)
    record_info(ws, cpu, mem)
    r_c = row(cpu["used"], cpu["total"], "C")
    r_m = row(mem["used"], mem["total"], "M")
    
    return " ".join((r_c, r_m))

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
                
                help_win.addstr(0, 0, header(), WHITE_AND_BLACK)
                help_win.addstr(2, 0, example_map()[0], YELLOW_AND_BLACK)
                help_win.addstr(3, 0, example_map()[1], GREEN_AND_BLACK)
                help_win.addstr(4, 0, help_msg(), WHITE_AND_BLACK)
    
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

                window2.addstr(0, 0, header(), WHITE_AND_BLACK)

               
                with open(DAT_FILE) as infodat:
                    info = infodat.readlines()
                    for idx, graph in enumerate(sorted(info)):
                        if 'n/a' in graph: # red, if the node status is down or if numof cores used is > 52
                            window2.addstr(idx+2, 0, graph, RED_AND_BLACK)
                        #elif (float(node.split()[2])>52.00):
                        #    window2.addstr(idx+2, 0, node, RED_AND_BLACK)
                        #elif how_busy(node) >= 0.75: #if node is more than 75% full
                        #    window2.addstr(idx+2, 0, node, YELLOW_AND_BLACK)
                        else:
                            window2.addstr(idx+2, 0, graph, GREEN_AND_BLACK)
                window2.addstr(len(info)+2, 0, f'Last updated {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}', WHITE_AND_BLACK)
                window2.addstr(len(info)+3, 0, "Press q to quit, h for help OR any other key to refresh.", WHITE_AND_BLACK)
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
def fork_ssh(ws:str) -> None:
    '''
    Multiprocesses to ssh to each workstation and retrieve information 
    in parallel, significantly speeding up the process.
    '''
    global DAT_FILE, logger

    try:
        ws_lst = get_list_of_ws(ws)
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

        with open(DAT_FILE, 'a+') as infodat:
            try:
                data = prepare_data(ws)

                # each child process locks, writes to and unlocks the file
                fcntl.lockf(infodat, fcntl.LOCK_EX)
                infodat.write(f'{ws.ljust(7)} {data}\n')
                infodat.close()
                
            except Exception as e:
                logger.error(piddly(f"query of {ws} failed. {e}"))
                pass

            finally:
                logger.info(piddly(f"{ws} {data}"))
                os._exit(os.EX_OK)

    # make sure all the child processes finished before the function 
    # returns.
    while pids:
        # The zero in the argument means we wait for any child.
        # The resulting pid is the child that sent us a SIGCHLD.
        pid, exit_code, _ = os.wait3(0) 
        pids.remove(pid)

@trap
def wsview_main() -> int: 
    #print(get_memory("thais"))
    #print(get_cpu("adam"))
    #get_list_of_ws("all")
    #record_info("adam")
    #draw_data("parish")
    fork_ssh("parish")
    wrapper(display_data)
    return os.EX_OK







if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="activityview",
        description="What activityview does, activityview does best.")
    parser.add_argument('-r', '--refresh', type=int, default=60,
        help="Refresh interval defaults to 60 seconds. Set to 0 to only run once.")
    parser.add_argument('-i', '--input', type=str, default="wscontrol.toml",
        help="If present, --input is interpreted to be a whitespace delimited file of host names.")
    parser.add_argument('--db', type=str, default="wscontrol.db",
        help="The program will insert data into the database.")
    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    parser.add_argument('-v', '--verbose', type=int, default=logging.DEBUG,
        help=f"Sets the loglevel. Values between {logging.NOTSET} and {logging.CRITICAL}.")


    myargs = parser.parse_args()

    verbose = myargs.verbose if logging.NOTSET <= myargs.verbose <= logging.CRITICAL else logging.DEBUG
    logger = wsview_utils.URLogger(level=myargs.verbose)
    try:
        db = sqlitedb.SQLiteDB(myargs.db)
    except:
        db = None
        print(f"Unable to open {myargs.db}")
        sys.exit(EX_CONFIG)
    #print("??", db)

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"]())

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")
