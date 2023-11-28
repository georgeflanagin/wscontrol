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
from   enum import IntEnum

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

    # Actions to take if there are problems.
    IGNORE = 8
    FAIL = 9
    NEXT = 10
    RETRY = 11

    # Instructions to "do something" or "identify something"
    CAPTURE     = 16
    FROM        = 17
    DO          = 18
    ON          = 19
    SEND        = 20
    ONERROR     = 21
    EXEC        = 22
    TO          = 23
    LOCAL       = 24
    REMOTE      = 25
    FILES       = 26
    LITERAL     = 27
    

    # Atomic instructions that can appear anywhere. The
    # NOP instruction can replace any of the others, effectively
    # commenting out a portion of the code.
    NOP = 126
    STOP = 125
    LOG = 124

###
# Parsers for keywords and delimiters.
###
at_sign = lexeme(string(AT_SIGN))
comma   = lexeme(string(COMMA))
do      = lexeme(string('do'))
local   = lexeme(string('local'))
lparen  = lexeme(string(LPAREN))
on      = lexeme(string('on'))
rparen  = lexeme(string(RPAREN))
send    = lexeme(string('send'))
to      = lexeme(string('to'))

###
# A parser to turn an action word into an opcode.
###
action = ( lexeme(string('ignore')).result(OpCode.IGNORE) | 
            lexeme(string('fail')).result(OpCode.FAIL) | 
            lexeme(string('next')).result(OpCode.NEXT) | 
            lexeme(string('retry')).result(OpCode.RETRY) )

###
# Host names are alpha+underscore
# Filenames also allows dashes, and bash symbols.
###
hostname = lexeme(regex('[A-Za-z_]+'))
filename = lexeme(regex('[A-Za-z/\.-_$~]+'))

@lexeme
@generate
def hostnames():
    """
    Example: (adam, anna)
    """
    yield WHITESPACE
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
    yield WHITESPACE
    yield capture
    cmd = yield op
    raise EndOfGenerator((OpCode.CAPTURE, cmd))

any_op = capture_op ^ op

@lexeme
@generate 
def op_sequence():
    """
    Example: (capture "tail -1 /etc/fstab", 
        "sed -i 's/141.166.88.99/newhost/' somefile")
    """
    yield WHITESPACE
    yield lparen
    ops = yield sepBy(any_op, comma)
    yield rparen
    raise EndOfGenerator(ops)


@lexeme
@generate
def from_file_clause():
    """
    Example: from someremotefile.txt
             from local somefile.txt
    """
    yield WHITESPACE
    yield lexeme(string('from'))
    local_scope = yield optional(local)
    fname = yield filename
    raise EndOfGenerator((OpCode.FROM, 
        OpCode.LOCAL if local_scope else OpCode.REMOTE,
        fname))


@lexeme
@generate
def on_error_clause():
    """
    Example: on_error fail
    """
    yield WHITESPACE
    yield lexeme(string('on_error'))
    error_action = yield action
    raise EndOfGenerator((OpCode.ONERROR, error_action))


@lexeme
@generate
def do_clause():
    yield WHITESPACE
    yield do
    action = yield from_file_clause ^ capture_op ^ op_sequence ^ op
    raise EndOfGenerator((OpCode.DO, action))

    
@lexeme
@generate
def exec_command():
    """
    Example: on parish_lab_computers do "dnf -y update"
    """
    yield WHITESPACE
    yield on
    location = yield context
    location = ((OpCode.ON, location))
    action = yield do_clause
    error_action = yield optional(on_error_clause, (OpCode.ONERROR, OpCode.FAIL))
    raise EndOfGenerator((OpCode.EXEC, location, action, error_action))


@lexeme
@generate
def send_command():
    """
    Example: send /some/files/*.txt to all_workstations
    """
    yield WHITESPACE
    yield lexeme(string('send'))
    fname = yield filename
    fname = (OpCode.FILES, fname)
    yield lexeme(string('to'))
    destination = yield context
    destination = (OpCode.TO, destination)
    action = yield optional(on_error_clause, ('ONERROR', 'fail'))
    raise EndOfGenerator((OpCode.SEND, fname, destination, action))


@lexeme
@generate
def log_command():
    """
    Log a message.
    """
    yield WHITESPACE
    yield lexeme(string('log'))
    text = yield quoted ^ everything
    raise EndOfGenerator((OpCode.LOG, (OpCode.LITERAL, text)))

stop_command = WHITESPACE >> lexeme(string('stop')).result(OpCode.STOP) ^ lexeme(string('quit')).result(OpCode.STOP)
nop_command  = WHITESPACE >> lexeme(string('nop')).result(OpCode.NOP) + \
    (stop_command ^ log_command ^ send_command ^ exec_command)

wslanguage = WHITESPACE >> nop_command ^ stop_command ^ log_command ^ send_command ^ exec_command

@trap
def make_tree(opcodes:tuple) -> SloppyTree:
    """
    Run down the opcodes, and build a tree so that we can use the 
    usual tree functions to find things. 
    """
    t = SloppyTree()
    try:
        command, instructions = opcodes
    except:
        return t[opcodes]

    for opcode in instructions:
        if isinstance(opcode, tuple):
            t[command][opcode[0]] = opcode[1:]
        else:
            t[command][opcode]
    return t


@trap
def parser_test(p:Parser, s:str) -> int:
    """
    For testing. Pick a parser and a string and print the result or
    the error.
    """
    print(f"Parsing >>{s}<<")
    result = p.parse(s)
    print(f"{result=}\n")
    return os.EX_OK


if __name__ == '__main__':

    parser_test(wslanguage, 'stop')
    parser_test(wslanguage, '  stop   ')
    parser_test(wslanguage, '  stop')
    parser_test(hostname, "adam" )
    parser_test(hostname, "adam " )
    parser_test(hostnames, "(adam, anna)")
    parser_test(context, "(adam, anna, michael)")
    parser_test(context, "michael")
    parser_test(context, "(michael)")
    parser_test(send_command, "send /ab/c/d to (adam, anna, kevin)")
    parser_test(exec_command, 'on parish_lab_workstations do "date -%s"')
    parser_test(exec_command, 'on (billieholiday, badenpowell) do "date -%s"')

    parser_test(wslanguage, 'on (sarah, evan, kevin) do "cat /etc/fstab")')   
    parser_test(wslanguage, 'on (sarah, evan, kevin) do capture "cat /etc/fstab")')   
    parser_test(wslanguage, """
        on (billieholiday, adam, thais) do (
            capture "tail -1 /etc/fstab", 
            "sed -i 's/141.166.88.99/newhost/' somefile" )
            """)

    parser_test(wslanguage, """on adam do from x.sh""")
    parser_test(wslanguage, """on adam do from local ~/X.sh""")
    parser_test(wslanguage, """send ~/important.txt to all_workstations""")

    parser_test(wslanguage, """log "hello world" """)
    
