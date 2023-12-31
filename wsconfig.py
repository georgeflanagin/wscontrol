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
import logging
import tomllib

###
# Installed libraries.
###


###
# From hpclib
###
from   sloppytree import SloppyTree
from   urdecorators import trap
from   urlogger import URLogger

###
# imports and objects that are a part of this project
###


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

logger = logging.getLogger('URLogger')

class WSConfig:
    _config = None

    @trap
    def __new__(cls, *args, **kwargs):
        if cls._config: return cls._config

        if not os.path.exists(args[0]):
            logger.error(f"{args[0]} not found.")
            sys.exit(os.EX_IOERR)

        try:
            cls._config = SloppyTree(tomllib.load(open(myargs.config, 'rb')))
            logger.info(f"{myargs.config} read.")

        except tomllib.TOMLDecodeError as e:
            logger.error(e)
            sys.exit(os.EX_CONFIG)
        
            

