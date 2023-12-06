# -*- coding: utf-8 -*-
"""
wscontrol is a utility to allow control over a group of 
Linux workstations in a command line environment. 
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
import argparse
import contextlib
import getpass
import logging
import tomllib

###
# Installed libraries.
###


###
# From hpclib
###
import linuxutils
from   sloppytree import SloppyTree
import sqlitedb
from   sqlitedb import SQLiteDB
from   urdecorators import trap
from   urlogger import URLogger, piddly

###
# imports and objects that are a part of this project
###
from wsconsole import WSConsole


###
# Global objects and initializations
###
logger=None
mynetid = getpass.getuser()

###
# Credits
###
__author__ = 'George Flanagin, João Tonini'
__copyright__ = 'Copyright 2023'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'George Flanagin, João Tonini'
__email__ = ['gflanagin@richmond.edu', 'jtonini@richmond.edu']
__status__ = 'in progress'
__license__ = 'MIT'


@trap
def wscontrol_main(myargs:argparse.Namespace) -> int:
    global logger
    logger.info("start")

    ###
    # Step 1: get the database open.
    ###
    if not os.path.exists(myargs.db):
        logger.error(f"{myargs.db} does not exist.")
        sys.exit(os.EX_IOERR)

    db = SQLiteDB(myargs.db)
    if not db.OK: 
        logger.error(f"unable to open {myargs.db}")
        sys.exit(os.EX_CONFIG)
    logger.info(f"{myargs.db} is open.")

    ###
    # Step 2: read the configuration.
    ###
    if not os.path.exists(myargs.config):
        logger.error(f"{myargs.config} not found.")
        sys.exit(os.EX_IOERR)

    try:
        config = SloppyTree(tomllib.load(open(myargs.config, 'rb')))
        logger.info(f"{myargs.config} read.")

    except tomllib.TOMLDecodeError as e:
        logger.error(e)
        sys.exit(os.EX_CONFIG)
    
    ###
    # Step 3: create the interactive console, and begin to read
    # the input.
    console=WSConsole(myargs, config, db)
    try:
        console.cmdloop(intro=f"Welcome to WSControl. Version {linuxutils.version(False)}")
    except KeyboardInterrupt as e:
        print("You pressed control-C")
        logger.info("Leaving via control-C")
        sys.exit(os.EX_OK)

    except Exception as e:
        logger.error(e)
        sys.exit(os.EX_IOERR)
    
    logger.info("Normal termination.")
    return os.EX_OK


if __name__ == '__main__':

    here       = os.getcwd()
    progname   = os.path.basename(__file__)[:-3]
    configfile = f"{here}/{progname}.toml"
    database   = f"{here}/{progname}.db"
    logfile    = f"{here}/{progname}.log"
    
    parser = argparse.ArgumentParser(prog=progname, 
        description=f"What {progname} does, {progname} does best.")

    parser.add_argument('--db', type=str, default=database,
        help=f"Name of the wscontrol database, defaults to {database}")

    parser.add_argument('--config', type=str, default=configfile,
        help=f"Input config file name, defaults to {configfile}")

    parser.add_argument('--loglevel', type=int,
        choices=range(logging.FATAL, logging.NOTSET, -10), 
        default=logging.DEBUG, 
        help=f"Logging level, defaults to {logging.DEBUG}")

    parser.add_argument('--no-exec', action='store_true', 
        help="For testing; this generates all the opcodes, but does not execute the command.")

    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name (for non-interactive use.)")

    parser.add_argument('-z', '--zap', action='store_true', 
        help=f"Remove {logfile} and create a new one.")

    myargs = parser.parse_args()
    if myargs.zap:
        try:
            os.unlink(logfile)
        finally:
            pass

    logger = URLogger(logfile=logfile, level=myargs.loglevel)

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{progname}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

