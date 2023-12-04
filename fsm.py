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
from   dorunrun import dorunrun
import linuxutils
from   sloppytree import SloppyTree
from   urdecorators import trap

###
# imports and objects that are a part of this project
###
from wscontrolparser import OpCode

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


@trap
def prep_command(t:SloppyTree) -> str:
    return ""


@trap
def prep_connection(t:SloppyTree) -> str:
    return ""


@trap
def prep_destination(t:SloppyTree) -> str:
    return ""


jump_table = {
    OpCode.DO : prep_command,
    OpCode.ON : prep_connection,
    OpCode.TO : prep_destination
    }



@trap
def fsm(prog:SloppyTree) -> int:
    """
    Execute the user's request
    """
    request_type = next(iter(dict(prog)))
    

    result = SloppyTree(dorunrun(cmd, timeout=t, return_datatype=dict))
    return os.EX_OK

