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
from   collections.abc import Iterable
import contextlib
import getpass
mynetid = getpass.getuser()
import logging

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
logger = logging.getLogger('URLogger')
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
def prep_command(t:Iterable) -> str:
    return f"""'{t}'"""


@trap
def prep_connection(t:SloppyTree) -> str:
    h = t.hostname
    u = t.user
    return f"""ssh -o ConnectTimeout=5 {u}@{h} """"


@trap
def prep_destination(t:SloppyTree) -> str:
    return ""


@trap
def fsm(prog:SloppyTree) -> int:
    """
    Execute the user's request
    """
    request_type = next(iter(dict(prog)))

    if request_type is not OpCode.EXEC:
        return os.EX_OK

    for target in prog[OpCode.ON]:
        target_string = prep_connection(target)
        for action in prog[OpCode.DO]:
            action_string = prep_command(action):
            cmd = f"{target_string} {action_string}"
            logger.debug(cmd)
            result = SloppyTree(dorunrun(cmd, timeout=t, return_datatype=dict))
            if not result.OK:
                pass 

    return os.EX_OK

