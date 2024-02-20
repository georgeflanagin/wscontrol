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
import time

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
    object_created = None
    config_file = None

    @trap
    def __new__(cls, *args, **kwargs):

        # Figure out how we are being called and if any of this will work
        # like it should. If called without any arguments, we are just
        # getting information that is already present.
        if not WSConfig.object_created:
            if not len(args):
                print("No config information.")
                sys.exit(os.EX_CONFIG)
        
            cls.read_toml_data(args[0])

        else:
            config_file_modified = os.path.getmtime(WSConfig.config_file)
            if config_file_modified > WSConfig.object_created:
                cls.read_toml_data(WSConfig.config_file)
             
        return WSConfig._config

    @classmethod 
    def read_toml_data(cls, filename:str) -> None:
        try:
            WSConfig._config = SloppyTree(tomllib.load(open(filename, 'rb')))
            WSConfig.object_created = time.time()
            WSConfig.config_file = filename

        except tomllib.TOMLDecodeError as e:
            logger.error(e)
            print(f"Bad TOML file {filename}")
            sys.exit(os.EX_CONFIG)

        except Exception as e:
            logger.error(f"{filename} not found.")
            sys.exit(os.EX_IOERR)
            

if __name__ == "__main__":
    myargs = MyArgs()
    
    # Instantiate WSConfig to load the configuration
    config_instance = WSConfig(myargs.config)
    print(config_instance)
