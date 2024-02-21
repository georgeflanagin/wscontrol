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
from   collections.abc import Iterable
import contextlib
import getpass
mynetid = getpass.getuser()
import logging
import socket
this_host = socket.gethostname()

###
# Installed libraries.
###


###
# From hpclib
###
from   dorunrun import dorunrun
import linuxutils
from   sloppytree import SloppyTree
import sqlitedb
from   urdecorators import trap

###
# imports and objects that are a part of this project
###
from opcodes import OpCode
from wsview import * #utility for a snapshot
###
# Global objects and initializations
###
logger = logging.getLogger('URLogger')
verbose = False
SQL = """INSERT INTO master (who, host, command, result) VALUES (?, ?, ?, ?)"""

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2023'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'George Flanagin'
__email__ = ['gflanagin@richmond.edu']
__status__ = 'in progress'
__license__ = 'MIT'

statements = SloppyTree()
statements.get_memory = lambda ws : f"ssh -o ConnectTimeout=1 {ws} free"
statements.get_proc = lambda ws : f"ssh -o ConnectTimeout=1 {ws} nproc"
statements.in_use = lambda ws : f"ssh -o ConnectTimeout=1 {ws} w"


@trap
def prep_action(t:Union[tuple, str]) -> tuple:
    """
    The command string itself may have different kinds of quotes
    in it.
    """
    if isinstance(t, str): t=(t,)
    t = tuple(s.replace('"', '\\"') for s in t)
    return " && ".join(t)


@trap
def prep_connection(t:SloppyTree) -> str:
    h = t.hostname
    u = t.user
    k = t.identityfile[0]
    return f"""ssh -i {k} -o ConnectTimeout=5 {u}@{h} """


@trap
def prep_destination(t:SloppyTree) -> str:
    return ""


@trap
def fsm(prog:SloppyTree, exec:bool) -> int:
    """
    Execute the user's request
    """
    request_type = next(iter(dict(prog)))
    prog = prog[request_type]

    foo = f"fsm_do_{request_type.name}"
    return globals()[foo](prog, exec)


@trap
def fsm_do_EXEC(prog:SloppyTree, exec:bool) -> int:
    """
    prog -- the instructions of the program, now that we have
        determined the type of request.
    exec -- must be True to execute the command. This is to support
        testing and dry-run functionality.
    """

    global mynetid, this_host
    db = sqlitedb.SQLiteDBinstance()

    ###
    # A nested loop across each command to be executed first, and
    # then looping over the hosts. The reason is that the command
    # is invariant across the hosts, and there is no need to rebuild
    # it for each one.
    ###
    num_actions = 0
    for action in prog[OpCode.DO]:
        action_string = prep_action(action)
        for target in prog[OpCode.ON]:
            target_string = prep_connection(SloppyTree(target))
            cmd = f"{target_string} {action_string}"
            logger.debug(cmd)
                    
            if exec:
                print(cmd)
                result = SloppyTree(dorunrun(cmd, timeout=5, return_datatype=dict))
                db.execute_SQL(SQL, mynetid, this_host, cmd, result.code)
                if result.OK: 
                    num_actions +=1 
                    print(result.stdout)
                    continue
                if prog[OpCode.ONERROR] == OpCode.FAIL: 
                    sys.exit(result.code)
            else:
                result = print(cmd)

    return num_actions

@trap
def fsm_do_SNAPSHOT(prog:SloppyTree, db:SQLiteDB, exec:bool) -> int:
    """
    Snapshot is a program that displays CPU and memory availability using curses.
    """
    ws = "" #retrieve this from prog:SloppyTree
    fork_ssh(ws)
    wrapper(display_data)

@trap
def fsm_do_SEND(prog:SloppyTree, exec:bool) -> int:
    pass
