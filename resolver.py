# -*- coding: utf-8 -*-
import typing
from   typing import *

min_py = (3, 9)

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
from   glob import glob
import logging

###
# Installed libraries.
###


###
# From hpclib
###
import fileutils
import linuxutils
import netutils
from   sloppytree import SloppyTree
from   urdecorators import trap
from   urlogger import URLogger, piddly

###
# imports and objects that are a part of this project
###
from   opcodes import OpCode
from   wsconfig import WSConfig

###
# Global objects and initializations
###
verbose = False

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

all_hosts = netutils.get_ssh_host_info('all')
logger = logging.getLogger('URLogger')


@trap
def resplinter(t:object) -> object:
    for i, d in enumerate(t):
        for k, v in d.items():
            t[i] = splinter_table[k](v)
    return t

@trap
def resolve_config(search_term:str, not_found:object) -> object:
    """
    Look through our config information for a symbol.
    """
    d = WSConfig()
    for t in search_term.split('.'):    
        d = d.get(t)
        if d is None: return not_found
        
    return d
    
@trap
def resolve_ACTION(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_ACTIONS(t:object) -> object:
    return resplinter(t)

@trap
def resolve_CAPTURE(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_CONTEXT(t:object) -> object:
    """
    Make sense of host names.
    """
    return resplinter(t)

    
@trap
def resolve_DO(t:object) -> object:
    return t

@trap
def resolve_ERROR(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_EXEC(t:object) -> object:
    """
    EXEC is a root node of any tree where it appears. We just 
    preserve it, and resolve the branches in its tree. Other
    root node keys just point to this function because the 
    method of operation is identical.
    """
    return resplinter(t)

@trap
def resolve_FAIL(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_FILE(t:object) -> object:
    return fileutils.expandall(t)

@trap
def resolve_FILES(data:list) -> list:
    """
    FILES come in looking like these examples:

    One file: ('/ab/c/d',)
    Two files: (['/ab/c/d', '$HOME/.bashrc'],)

    Note that each is a one-tuple. 

    NOTE: Why not glob the filenames? There are two reasons that this
    does not work. [1] If nothing matches the globbed expression, glob
    returns an empty list. [2] Most of the programs like rsync and
    scp that might be used to move files between hosts deal well with
    wildcard file names.
    """
    if isinstance(data, dict):
        data = {k:splinter_table[k](v) for k, v in data.items()}

    else:
        for i, _ in enumerate(data):
            data[i] = {k:splinter_table[k](v) for k, v in _.items()}

    return data



@trap
def resolve_FROM(data:tuple) -> tuple:
    """
    FROM clause is part of a three-tuple. Only if it is a LOCAL
    file do we try to resolve the file name.
    """
    for k, v in data.items():
        data[k] = v if k is OpCode.REMOTE else splinter_table[k](v)
    return data

@trap
def resolve_HOST(t:object) -> object:
    """
    Transform t into something beyond its name.
    """
    newlist = []
    host = resolve_config(t, t)
    hosts = host if isinstance(host, list) else [host]
    for host in hosts:
        hostinfo = all_hosts.get(host)
        if hostinfo is None:
            print(f"No connection info for {host}")
            continue
        newlist.append({OpCode.HOST : hostinfo})
    return ({OpCode.CONTEXT : newlist})

@trap
def resolve_IGNORE(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_LITERAL(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_LOCAL(t:object) -> object:
    try:
        command_file = fileutils.expandall(clause[2])
        with open(command_file) as f:
            commands = f.readlines()
    except:
        print(f"Unable to open {command_file}")
        sys.exit(os.EX_IOERR)

    if not len(commands): 
        print(f"{command_file} is empty. Nothing to do.")
        return clause[0], clause[1], OpCode.NOP

    commands = tuple((OpCode.ACTION, _.strip()) for _ in commands if _)
    
    return clause[0], clause[1], commands


    return t

@trap
def resolve_LOG(t:object) -> object:
    return t

    # Nothing to do.
@trap
def resolve_NEXT(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_NOP(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_OK(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_ON(t:object) -> object:
    for k, v in t.items():
        t[k] = splinter_table[k](v)
    return t

@trap
def resolve_ONERROR(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_REMOTE(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_RETRY(t:object) -> object:
    # Nothing to do.
    return t

@trap
def resolve_SEND(t:object) -> object:
    return resplinter(t)

@trap
def resolve_SNAPSHOT(t:object) -> object:
    return t

@trap
def resolve_STOP(t:object) -> object:
    return lambda : sys.exit(os.EX_OK)

@trap
def resolve_TO(t:object) -> object:
    for k, v in t.items():
        t[k] = splinter_table[k](v)
    return t

@trap
def resolver(t:SloppyTree) -> SloppyTree:
    """
    This function works its way through the tree of symbols looking for
    ones that are un-resolved. Examples are: 

        - filenames that might contain environment variables like $HOME, 
            or that have relative paths like ../somedir/somefile.txt  
        - hostnames that are defined in ~/.ssh/config

    The resolver() goes through the tree and looks for OpCodes that 
    have resolvers identified by name: OpCode.ON -> resolve_ON, and so
    on. If they don't, then no changes are made.

    t -- The parse tree representing the user's command.

    returns -- The modified (resolved) parse tree.

    """
    for k, v in t.items():
        try:
            t[k] = splinter_table[k](v)
        except Exception as e:
            print(f"Found non OpCode key {k} giving error {e}")
    return t

###
# This is the splinter table for the OpCodes.
###
splinter_table = dict.fromkeys((_.value for _ in OpCode), None)
for _ in OpCode:
    try:
        splinter_table[_] = globals()[f"resolve_{_.name}"]
    except:
        print(f"{_} has no assocated function.")
    

