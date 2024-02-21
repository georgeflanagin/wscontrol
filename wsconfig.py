# -*- coding: utf-8 -*-
"""
WSConfig represents the object that contains all the configuration info
for the wscontrol program. It is read from a .toml file, like this:

t = WSConfig('somefile.toml')

t is a SloppyTree created by code in the sloppytree module of hpclib.

As a part of the initialization, all of the leaves in the tree are examined
to see if they are strings that need conversion to lambda functions. This 
conversion is done via the staticmethod in this class, make_lambda.
"""
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
from   collections.abc import Callable
import logging
import re
import tomllib
import time

###
# Installed libraries.
###


###
# From hpclib
###
from   setutils import Universal
from   sloppytree import SloppyTree, deepsloppy
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
__copyright__ = 'Copyright 2024'
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
    pattern = re.compile(r'\{([^}]*)\}')

    @trap
    def __new__(cls, *args, **kwargs):

        # Figure out how we are being called and if any of this will work
        # like it should. If called without any arguments, we are just
        # getting information that is already present.
        if not WSConfig.object_created:
            if not len(args):
                print("No config information.")
                sys.exit(os.EX_CONFIG)
        
            cls.read_toml_data(args[0], kwargs)

        else:
            config_file_modified = os.path.getmtime(WSConfig.config_file)
            if config_file_modified > WSConfig.object_created:
                cls.read_toml_data(WSConfig.config_file, kwargs)
             
        return WSConfig._config

    @classmethod 
    def read_toml_data(cls, filename:str, kwargs:dict) -> None:
        try:
            WSConfig._config = deepsloppy(tomllib.load(open(filename, 'rb')))
            WSConfig.object_created = time.time()
            WSConfig.config_file = filename

        except tomllib.TOMLDecodeError as e:
            print(f"{e}")
            print(f"Error in the TOML file {filename}")
            sys.exit(os.EX_CONFIG)

        except FileNotFoundError as e:
            logger.error(f"{filename} not found.")
            sys.exit(os.EX_IOERR)

        except Exception as e:
            logger.error(f"{e}")
            print(e)
            sys.exit(os.EX_IOERR)

        # We have to set the updates aside for post-traversal correction to
        # avoid modifying the tree while we traverse it.
        updates={}
        branches = Universal() if kwargs.get('cmds') is None else kwargs['cmds']
        for branch in WSConfig._config.tree_as_table():
            if branch[-2] in branches:
                try:
                    v = WSConfig.make_lambda(branch[-1])
                    if isinstance(v, Callable):
                        updates[branch[:-1]] = v

                except Exception as e:
                    continue

        for k, v in updates.items():
            WSConfig._config[k] = v


    @staticmethod
    def make_lambda(s:str) -> Callable:
        """
        Examine s for brace pairs, extract the text between the 
        braces, and create a lambda function from the information.
        """
        args = re.findall(WSConfig.pattern, s)
        if not args: return s

        args = ",".join(set(args))
        text = f"""lambda {args} : "{s}" """
        return eval(text)


if __name__ == "__main__":
    
    # Instantiate WSConfig to load the configuration
    try:
        config_instance = WSConfig(sys.argv[1])
    except:
        config_instance = WSConfig('wscontrol.toml')

    t = config_instance
    print(t)
