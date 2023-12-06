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
import logging
from   pprint import pprint
import socket
this_host = socket.gethostname()

###
# Installed libraries.
###


###
# From hpclib
###
import linuxutils
import parsec4
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


logger = logging.getLogger('URLogger')

SQL = """INSERT INTO master (who, host, command) VALUES (?, ?, ?)"""


class WSConsole(cmd.Cmd):
    
    def __init__(self, 
        config:SloppyTree, 
        db:SQLiteDB, 
        logger:URLogger):

        cmd.Cmd.__init__(self)
        self.config = config
        self.db = db
        self.most_recent_cmd = ""
        self.logger = logger
        self.prompt = "[WSControl]: "


    @trap
    def construct_error_message(self, e:parsec4.ParseError) -> str:
        """
        Parsec does not provide very good error messages in its native
        format. The reason is that the monadic construction tends to
        conceal the overall picture. This function attempts to provide
        more information, and it is able to do so in most cases.
        """
        location = self.most_recent_cmd.find(e.text)
        
        if location == -1: 
            # We were unable to locate the error text. 
            return f"{e}"

        
        return "\n".join([e.text, " "*e.index + "^", "Excpected "+e.expected])
        

    @trap
    def do_help(self, args:str='') -> None:
        """
        Explain the program.
        """
        print("Put some help here.")


    @trap
    def default(self, args:str='') -> None:
        """
        This function has most of the error handling in it. Its purpose
        is to come as close as it can to pointing out the source of
        the problem in the command.
        """
        if not os.isatty(0):
            print(args)

        if args.lower() in ("stop", "quit", "exit"):
            sys.exit(os.EX_OK)

        try:
            self.most_recent_cmd = args
            tokens = wslanguage.parse(args)
        except KeyboardInterrupt as e:
            print("You pressed control C. Exiting.")
            sys.exit(os.EX_OK)

        except parsec4.ParseError as e:
            print("There is an error somewhere in your request.") 
            print(self.construct_error_message(e))  
            return
        
        resolved_command = resolver(self.config, make_tree(tokens))
        pprint(resolved_command)
        self.db.execute_SQL(SQL, mynetid, this_host, str(resolved_command))
