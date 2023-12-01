# -*- coding: utf-8 -*-
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
import argparse
import cmd
import contextlib
import getpass
mynetid = getpass.getuser()
from   pprint import pprint
###
# Installed libraries.
###


###
# From hpclib
###
import linuxutils
from   sloppytree import SloppyTree
from   sqlitedb import SQLiteDB
from   urdecorators import trap
from   urlogger import URLogger

###
# imports and objects that are a part of this project
###
from resolver import resolver
from wscontrolparser import wslanguage, make_tree

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


class WSConsole(cmd.Cmd):
    
    def __init__(self, 
        config:SloppyTree, 
        db:SQLiteDB, 
        logger:URLogger):

        cmd.Cmd.__init__(self)
        self.config = config
        self.db = db
        self.logger = logger
        self.prompt = "[WSControl]: "


    @trap
    def default(self, args:str='') -> None:
        if not os.isatty(0):
            print(args)

        if args.lower() in ("stop", "quit", "exit"):
            sys.exit(os.EX_OK)

        try:
            pprint(resolver(make_tree(wslanguage.parse(args))))
        except KeyboardInterrupt as e:
            print("You pressed control C. Exiting.")
            sys.exit(os.EX_OK)
        except Exception as e:
            print("There is an error somewhere in your request.") 
            
        

