# -*- coding: utf-8 -*-
import typing
from   typing import *

min_py = (3, 8)

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
    OK = 0

    IGNORE = 8
    FAIL = 9
    NEXT = 10
    RETRY = 11

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

action = ( lexeme(string('ignore')).result(OpCode.IGNORE) | 
            lexeme(string('fail')).result(OpCode.FAIL) | 
            lexeme(string('next')).result(OpCode.NEXT) | 
            lexeme(string('retry')).result(OpCode.RETRY) )

hostname = lexeme(regex('[A-Za-z]+'))
filename = lexeme(regex('[A-Za-z/\.-_]+'))

@lexeme
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

@lexeme
@generate
def capture_op():
    """
    Example: capture "an_action"
    """
    yield capture
    cmd = yield op
    raise EndOfGenerator(("CAPTURE", cmd))

any_op = capture_op | op

@lexeme
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


@lexeme
@generate
def from_file_clause():
    """
    Example: from somelocalfile.txt
    """
    yield lexeme('from')
    fname = yield string
    raise EndOfGenerator((OpCode.FROM, fname))


@lexeme
@generate
def on_error_clause():
    """
    Example: on_error fail
    """
    yield lexeme(string('on_error'))
    error_action = yield action
    raise EndOfGenerator((OpCode.ONERROR, error_action))

    
@lexeme
@generate
def exec_command():
    """
    Example: on parish_lab_computers do "dnf -y update"
    """
    yield lexeme(string('on'))
    location = yield context
    location = (OpCode.ON, location)
    yield lexeme(string('do'))
    ops = yield from_clause ^ op_sequence ^ op 
    ops = (OpCode.DO, ops)
    error_action = optional(on_error_clause, (OpCode.ONERROR, OpCode.FAIL))
    raise EndOfGenerator((OpCode.EXEC, 
        location, 
        ops, 
        error_action))


@lexeme
@generate
def send_command():
    """
    Example: send /some/files/*.txt to all_workstations
    """
    yield lexeme(string('send'))
    fname = yield filename
    yield lexeme(string('to'))
    destination = yield context
    action = yield optional(on_error_clause, ('ONERROR', 'fail'))
    raise EndOfGenerator((OpCode.SEND, fname, destination, action))


stop_command = lexeme(string('stop')).result(OpCode.STOP)
log_command = lexeme(string('log')).result(OpCode.LOG) + string

wslanguage = WHITESPACE >> stop_command ^ log_command ^ send_command ^ exec_command

@trap
def wscontrolparser(s:str) -> Union[int, tuple]:
    """
    Invoke the parser and then assemble the tokens in an
    orderly way.
    """
    try:
        result = wslanguage.parse(s)
    except Exception as e:
        return os.EX_DATAERR

    return tokens

@trap
def parser_test(p:Parser, s:str) -> int:
    """
    For testing. Pick a parser and a string and print the result or
    the error.
    """
    result = p.parse(s)
    print(f"{result=}\n")
    return os.EX_OK


if __name__ == '__main__':

    print(parser_test(hostname, "adam" ))
    print(parser_test(hostname, "adam " ))
    print(parser_test(hostnames, "(adam, anna)"))
    print(parser_test(context, "(adam, anna, michael)"))
    print(parser_test(context, "michael"))
    print(parser_test(context, "(michael)"))
    print(parser_test(send_command, "send /ab/c/d to (adam, anna, kevin)"))
