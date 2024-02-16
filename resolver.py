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

host_info = netutils.get_ssh_host_info('all')
logger = logging.getLogger('URLogger')

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
def resolve_CONTEXT(data:list)
    """
    Make sense of host names.
    """
    d = WSConfig()
    newlist = []
    for datum in data:
        host = datum[OpCode.HOST]
        host = resolve_config(host, host)
        hosts = host if isinstance(host, list) else [host]
        for host in hosts:
            hostinfo = info.get(host)
            if hostinfo is None:
                print(f"No connection info for {host}")
                continue
            newlist.append({OpCode.HOST : hostinfo})

    return newlist

    
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
    for i, datum in enumerate(data):
        data[i] = {datum[OpCode.FILE] : fileutils.expandall(datum[OpCode.FILE])}
    return data


def resolve_REMOTE(o:object) -> object:
    return o


@trap
def resolve_FROM(data:tuple) -> tuple:
    """
    FROM clause is part of a three-tuple. Only if it is a LOCAL
    file do we try to resolve the file name.
    """
    clause = data[0]
    print(clause)
    if clause[1] is not OpCode.LOCAL: return clause

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
    cmd = next(iter(dict(t)))
    d = t[cmd]

    for k in d.keys():
        if k in OpCode:
            try:
                d[k] = globals()[f"resolve_{k.name}"](d[k])
            except:
                d[k] = resolver(d[k])
        else:
            print(f"Found non-OpCode key {k}")
        
    t[cmd] = d
    return t

