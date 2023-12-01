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
from   wscontrolparser import OpCode

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
def resolve_FILES(data:tuple) -> tuple:
    """
    FILES come in looking like these examples:

    One file: ('/ab/c/d',)
    Two files: (['/ab/c/d', '$HOME/.bashrc'],)

    Note that each is a one-tuple. 
    """
    files = data[0]
    if isinstance(files, str): files = (files,)
    return tuple(fileutils.expandall(_) for _ in files)

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
    if OpCode.FROM in data[0]:
        return resolve_FROM(data)
    
@trap
def resolve_ON(data:tuple) -> tuple:
    """
    hostnames come in looking like this:

    (['adam', 'anna', 'kevin'],)
    """
    global info
    hosts = data[0]
    if isinstance (hosts, str): hosts = (hosts,)
    
    # First, determine if the name is really a host name
    # or if it is something else. 
    for host in hosts:
        if host not in info:
            pass    

    return tuple(info.get(_, _) for _ in hosts)
    

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

    """
    cmd = next(iter(dict(t)))
    d = t[cmd]

    for k in d.keys():
        logger.debug(f"{k=}")
        if k in OpCode:
            try:
                logger.debug(f"resolve_{k.name}")
                logger.debug(f"{d[k]=}")
                d[k] = globals()[f"resolve_{k.name}"](d[k])
            except:
                logger.info(f"No resolver for resolve_{k.name}")                
                pass

        else:
            logger.info(f"{k=} not in OpCode")
            pass # someday, we may have something else here.
        
    t[cmd] = d
    return t


