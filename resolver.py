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

info = netutils.get_ssh_host_info('all')
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
def resolve_FILES(data:tuple) -> tuple:
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
    files = data[0]
    if isinstance(files, str): files = (files,)
    return tuple((OpCode.FILE, fileutils.expandall(_)) for _ in files)


@trap
def resolve_FROM(data:tuple) -> tuple:
    """
    FROM clause is part of a three-tuple. Only if it is a LOCAL
    file do we try to resolve the file name.
    """
    clause = data[0]
    if clause[1] is OpCode.LOCAL:
        return clause[0], clause[1], fileutils.expandall(clause[2])
    else:
        return clause


@trap
def resolve_DO(data:tuple) -> tuple:
    if OpCode.FROM.name in data[0]:
        return resolve_FROM(data)
    return data[0]

    
@trap
def resolve_ON(data:tuple) -> tuple:
    """
    hostnames come in looking like this:

    (['adam', 'anna', 'kevin'],)
    ('adam',)
    """
    global info
    data = data[0]
    
    if isinstance (data, str): data = (data,)

    connection_info = []
    for datum in data:
        hosts = resolve_config(datum, (datum,))
        for host in hosts:
            hostinfo = info.get(host)
            if hostinfo is None:
                print(f"No connection information for {host}.")
                sys.exit(os.EX_CONFIG)
            connection_info.append((OpCode.HOST, hostinfo))
    
    return connection_info

resolve_TO = resolve_ON


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
    try:
        config = WSConfig()
    except Exception as e:
        print(f"Could not get configuration. {e}")
        sys.exit(os.EX_CONFIG)

    cmd = next(iter(dict(t)))
    d = t[cmd]

    for k in d.keys():
        if k in OpCode:
            try:
                d[k] = globals()[f"resolve_{k.name}"](d[k])
            except:
                pass

        else:
            logger.info(f"{k=} not in OpCode")
            pass # someday, we may have something else here.
        
    t[cmd] = d
    return t

