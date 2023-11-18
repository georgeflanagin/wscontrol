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
import contextlib
from   enum import IntEnum
import getpass
mynetid = getpass.getuser()

###
# Installed libraries.
###


###
# From hpclib
###
import linuxutils
import parsec4
from   parsec4 import *
from   sloppytree import SloppyTree
from   urdecorators import trap

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


class OpCode(IntEnum):
    IGNORE = 0
    OK = 0
    FAIL = 127
    NEXT = 1
    RETRY = 2

    CAPTURE = 16
    FROM = 17
    DO = 18
    ON = 19
    SEND = 20
    ONERROR = 21
    EXEC = 22


    NOP = 126
    STOP = 125
    LOG = 124


lparen = lexeme(string(LPAREN))
rparen = lexeme(string(RPAREN))
at_sign = lexeme(string(AT_SIGN))
comma = lexeme(string(COMMA))

login = string + at_sign + string

action = ( lexeme(string('ignore')).result(OpCode.IGNORE) | 
            lexeme(string('fail')).result(OpCode.FAIL) | 
            lexeme(string('next')).result(OpCode.NEXT) | 
            lexeme(string('retry')).result(OpCode.RETRY) )

hostname = lexeme(string)

@generate
def hostnames():
    """
    Example: (adam, anna)
    """
    yield lparen
    elements = yield sepBy(hostname, comma)
    yield rparen
    raise EndOfGenerator(elements)

context = hostnames ^ hostname

op = quoted
capture = lexeme(string('capture'))

@generate
def capture_op():
    """
    Example: capture "an_action"
    """
    yield capture
    cmd = yield op
    raise EndOfGenerator(("CAPTURE", cmd))

any_op = capture_op | op

@generate 
def op_sequence():
    """
    Example: (capture "tail -1 /etc/fstab", 
        "sed -i 's/141.166.88.99/newhost/' somefile")
    """
    yield lparen
    ops = yield sepBy(any_op, comma)
    yield rparen
    raise EndOfGenerator(ops)


@generate
def from_file_clause():
    """
    Example: from somelocalfile.txt
    """
    yield lexeme('from')
    fname = yield string
    raise EndOfGenerator((OpCode.FROM, fname))


@generate
def on_error_clause():
    """
    Example: on_error fail
    """
    yield lexeme(string('on_error'))
    error_action = yield action
    raise EndOfGenerator((OpCode.ONERROR, error_action))

    
@generate
def exec_command():
    """
    Example: on parish_lab_computers do "dnf -y update"
    """
    yield lexeme('on')
    location = yield context
    yield lexeme('do')
    ops = yield from_clause ^ op_sequence ^ op 
    error_action = optional(on_error_clause, (OpCode.ONERROR, OpCode.FAIL))
    raise EndOfGenerator((OpCode.EXEC, 
        location, 
        ops, 
        error_action))


@generate
def send_command():
    """
    Example: send /some/file to all_workstations
    """
    yield lexeme('send')
    filename = yield string
    yield lexeme('to')
    destination = yield context
    error_action = optional(on_error_clause, ('ONERROR', 'fail'))
    raise EndOfGenerator(('SEND', filename, destination, error_action))


stop_command = lexeme(string('stop')).result(OpCode.STOP)
log_commmand = lexeme(string('log')).result(OpCode.LOG) + string


@trap
def wscontrolparser_main(myargs:argparse.Namespace) -> SloppyTree:
    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="wscontrolparser", 
        description="What wscontrolparser does, blather does best.")

    parser.add_argument('-i', '--input', type=str, default="",
        help="Input file name.")
    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    parser.add_argument('-v', '--verbose', action='store_true',
        help="Be chatty about what is taking place")


    myargs = parser.parse_args()
    verbose = myargs.verbose

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

