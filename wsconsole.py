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
import inspect
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
import netutils
import parsec4
from   sloppytree import SloppyTree
import sqlitedb
from   urdecorators import trap
from   urlogger import URLogger

###
# imports and objects that are a part of this project
###
#from fsm import fsm
from resolver import resolver
from wscontrolparser import wslanguage
from wsconfig import WSConfig

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

SQL = """INSERT INTO master (who, host, command, result) VALUES (?, ?, ?, ?)"""


class WSConsole(cmd.Cmd):
    
    def __init__(self, myargs:argparse.Namespace):

        cmd.Cmd.__init__(self)
        self.myargs = myargs
        self.most_recent_cmd = ""
        self.prompt = "\n [WSControl]: "


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

        
        return "\n".join([e.text, " "*e.index + "^", "Expected: "+e.expected])
        

    @trap
    def do_general(self, args:str='') -> None:
        """
        Explain the program.
        """
        text="""
    
    This program supports autocomplete via the TAB key. Also, if you want
    to execute a shell command from within the program, wscontrol interprets
    anything that starts with a bang (!) as a shell command.

    Type in a command to have it parsed and executed. Here are some examples:

      on billieholiday do "date"

    This command will look up the information about the host "billieholiday"
    and execute the Linux "date" command on that computer. Here is a slightly
    more complex command.

      on ws.provost do ("tail -1 /etc/fstab", "date")

    The program will look up ws.provost and discover that it means all the
    workstations owned by the Provost Office. On each of those computers,
    it will then execute the two commands shown, in the order that they
    appear.

    """
        print(text)


    @trap
    def do_samples(self, args:str="") -> None:
        """
        Show some samples.
        """
        return


    @trap
    def do_whatis(self, args:str="") -> None:
        """
        Syntax: whatis {symbol}
    
        Look up a symbolic name (example: the name of a host or 
        group of hosts), and show the user what it means.
        """ 
        if not args: return self.do_help('whatis')

        arg_list = args.split('.')
        t = WSConfig()
        for arg in arg_list:
            try:
                t = t[arg]
            except KeyError as e:
                print(f"{args} not found in config file.")
                return

        if t: 
            print(f"{args} is {t}")
            return

        if (d:=netutils.get_ssh_host_info(args)):
            print(f"{args} is a host, with this connection information:\n\n{d}")
            return

        print(f"{args} must not be a piece of config data.")


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

        if args.startswith('!'):
            os.system(args[1:])
            return

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
        
        resolved_command = resolver(tokens)
        logger.debug(f"{resolved_command=}")
        pprint(f"{resolved_command=}")
        # fsm(resolved_command, not self.myargs.no_exec)
