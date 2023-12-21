# -*- coding: utf-8 -*-
"""
This file contains methods and classes that activity-view relies on.
"""

import typing
from   typing import *

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2022, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'Alina Enikeeva'
__email__ = 'alina.enikeeva@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'


###
# Standard imports, starting with os and sys
###
min_py = (3, 8)
import enum
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
import shlex
import subprocess
import logging
from   logging.handlers import RotatingFileHandler
import pathlib
import math
import pprint
from   functools import reduce

from   wrapper import trap

padding = lambda x: " "*x

################### logging utility begin #################
def piddly(s:str) -> str:
    """
    A text wrapper for logging the output of multithreaded and
    multiprocessing programs.

    Example: 

        logger=URLogger()
        logger.info(piddly(msg))
    """
    return f": {os.getppid()} <- {os.getpid()} : {s}"

class URLogger: pass

class URLogger:
    __slots__ = {
        'logfile': 'the logfile associated with this object',
        'formatter': 'format string for the logging records.', 
        'level': 'level of the logging object',
        'rotator': 'using the built-in log rotation system',
        'thelogger': 'the logging object this class wraps'
        }

    __values__ = (
        None,
        logging.Formatter('#%(levelname)-8s [%(asctime)s] (%(process)d) %(module)s: %(message)s'),
        logging.WARNING,
        None,
        None)

    __defaults__ = dict(zip(__slots__.keys(), __values__))

    def __init__(self, **kwargs) -> None:

        # Set the defaults.
        for k, v in URLogger.__defaults__.items():
            setattr(self, k, v)

        # Override the defaults if needed.
        for k, v in kwargs.items(): 
            if k in URLogger.__slots__:
                setattr(self, k, v)
        
        try:
            if self.logfile is None:
                self.logfile=os.path.join(os.getcwd(), "thisprog.log")
            pathlib.Path(self.logfile).touch(mode=0o644, exist_ok=True)

        except Exception as e:
            sys.stderr.write(f"Cannot create or open {self.logfile}. {e}\n")
            raise e from None

        self.rotator = RotatingFileHandler(self.logfile, maxBytes=1<<24, backupCount=2)
            
        self.rotator.setLevel(self.level)
        self.rotator.setFormatter(self.formatter)

        # setting up logger with handlers
        self.thelogger = logging.getLogger('URLogger')
        self.thelogger.setLevel(self.level)
        self.thelogger.addHandler(self.rotator)


    ###
    # These properties provide an interface to the built-in
    # logging functions as if the class member, self.thelogger,
    # were exposed. 
    ###
    @property
    def debug(self) -> object:
        return self.thelogger.debug

    @property
    def info(self) -> object:
        return self.thelogger.info

    @property
    def warning(self) -> object:
        return self.thelogger.warning

    @property
    def error(self) -> object:
        return self.thelogger.error

    @property
    def critical(self) -> object:
        return self.thelogger.critical


    ###
    # Tinker with the object model a little bit.
    ###
    def __str__(self) -> str:
        """ return the name of the logfile. """
        return self.logfile


    def __int__(self) -> int:
        """ return the current level of logging. """
        return self.level


    def __call__(self, level:int) -> URLogger:
        """
        reset the level of logging, and return 'self' so that
        syntax like this is possible:

            mylogger(logging.INFO).info('a new message.')
        """
        self.level = level
        self.rotator.setLevel(self.level)
        self.thelogger.setLevel(self.level)
        return self 
###################### logger utility end ###################


##################### ncurses utility begin ################

@trap
def header():
    """
    The header of the window.
    """
    header = "WS".ljust(8)+"Cores"+padding(38)+"Memory\n"
    return header

@trap
def help_msg() -> str:
    """
    Write help message here.
    """

    a = "\nThis program displays availability of workstations (WS).\n\n"
    b = "Next to the name of the WS, you can see the graphs.\n"
    c = "The first graph is displaying availability of CPUs.\n"
    d = "The second graph is displaying memory availability.\n\n"
    e = "If the graph is colored in green, that means that its load is less than 75% in terms of both memory and CPU usage.\n"
    f = "If the graph is colored yellow, that means that either WS's memory or CPUs are more than 75% occupied.\n"
    g = "The red color signifies anomaly - WS could not be accessed.\n"

    msg = "".join((a, b, c, d, e, f, g))

    return msg

@trap
def example_map():
    graph1 = "adam    [________________________________________] [MMMMMM__________________________________]"
    graph2 = "alexis  [________________________________________] [________________________________________]"

    return list((graph1, graph2))

######################## ncurses utility end ######################

######################## graphing utility begin ##################
@trap
def row(used:int, max_avail:int, x:str, scale:int=40, _:str="_", ends=('[', ']')) -> str:
    """
    used -- quantity to be filled with x.
    max_avail -- set of which used is a subset.
    scale -- if scale < max_avail, then used and max_avail are divided by scale.
    x -- the char used to show in-use-ness.
    _ -- the char used to show not-in-use-ness.
    ends -- decorators for start/finish.
    """
    try:
        used=int(used)
        max_avail=int(max_avail)
        scale=int(scale)
    except:
        raise Exception("numeric quantities are required")
    
    if not len(x) * len(_) * scale * max_avail:
        raise Exception("Cannot use zero length delimiters")

    if used < 0 or max_avail < 0 or scale < 0:
        raise Exception("quantities must be non-negative")

    used = max_avail if used > max_avail else used

    used = round(used * scale / max_avail)

    xes = used*x
    _s  = (scale-used)*_

    return f"{ends[0]}{xes}{_s}{ends[1]}"

####################### graphing utility end ####################
