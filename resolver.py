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

@trap
def resolve_ON(data:dict) -> SloppyTree:
    pass
    

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
        if k in OpCode:
            try:
                d[k] = globals()[f"resolve_{k.name}"](d[k])
            except:
                pass

        else:
            pass # someday, we have something else here.
        
    t[cmd] = d
    return t


