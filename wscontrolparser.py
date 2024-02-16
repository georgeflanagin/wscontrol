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
from   collections.abc import Iterable, Hashable
import contextlib
from   enum import IntEnum
from   pprint import pprint

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
from   parsertests import parsertests
from   opcodes import OpCode
import resolver
import wsconfig

###
# Global objects and initializations
###
use_resolver = False

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
snapshot = lexeme(string('snapshot'))

seq_pt  = lexeme(string(SEMICOLON))

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
hostname = lexeme(regex('[A-Za-z_.]+'))
filename = lexeme(regex('[-A-Za-z/.*_$~]+'))

@lexeme
@generate
def hostname():
    yield WHITESPACE
    name = yield lexeme(regex('[A-Za-z_.]+'))
    raise EndOfGenerator({OpCode.HOST: name})


@lexeme
@generate
def filename():
    yield WHITESPACE
    name = yield lexeme(regex('[-A-Za-z/.*_$~]+'))
    raise EndOfGenerator({OpCode.FILE: name})

@lexeme
@generate
def filenames():
    yield WHITESPACE
    yield lparen
    fnames = yield sepBy(filename, comma)
    yield rparen
    raise EndOfGenerator({OpCode.FILES: fnames})


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
    raise EndOfGenerator({OpCode.CONTEXT: elements})

context = hostnames ^ hostname

op = quoted

@lexeme
@generate
def any_op():
    """
    return a tagged action.
    """
    this_op = yield op
    raise EndOfGenerator({OpCode.ACTION: this_op})    


@lexeme
@generate 
def op_sequence():
    """
    Example: ("tail -1 /etc/fstab", 
        "sed -i 's/141.166.88.99/newhost/' somefile")
    """
    yield WHITESPACE
    yield lparen
    ops = yield sepBy(any_op, comma)
    yield rparen
    raise EndOfGenerator({OpCode.ACTIONS: ops})


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
    raise EndOfGenerator({OpCode.FROM : {
        OpCode.LOCAL if local_scope else OpCode.REMOTE :
        fname}})


@lexeme
@generate
def on_error_clause():
    """
    Example: on_error fail
    """
    yield WHITESPACE
    yield lexeme(string('on_error'))
    error_action = yield action
    raise EndOfGenerator({OpCode.ONERROR : error_action})


@lexeme
@generate
def snapshot_command():
    """
    Example: 
    """
    yield WHITESPACE
    yield snapshot 
    location = yield context
    location = {OpCode.ON : location}
    raise EndOfGenerator({OpCode.SNAPSHOT : location})


@lexeme
@generate
def do_clause():
    yield WHITESPACE
    yield do
    action = yield from_file_clause ^ op_sequence ^ op 
    raise EndOfGenerator({OpCode.DO : action})

    
@lexeme
@generate
def exec_command():
    """
    Example: on parish_lab_computers do "dnf -y update"
    """
    yield WHITESPACE
    yield on
    location = yield context
    location = {OpCode.ON: location}
    action = yield do_clause
    error_action = yield optional(on_error_clause, {OpCode.ONERROR: OpCode.FAIL})
    raise EndOfGenerator({OpCode.EXEC : [location, action, error_action]})


@lexeme
@generate
def send_command():
    """
    Example: send /some/files/*.txt to all_workstations
    """
    yield WHITESPACE
    yield lexeme(string('send'))
    print("send")
    fname = yield filenames ^ filename
    fname = {OpCode.FILES: fname}
    print(fname)
    yield lexeme(string('to'))
    destination = yield context
    destination = {OpCode.TO : destination}
    error_action = yield optional(on_error_clause, {OpCode.ONERROR: OpCode.FAIL})
    raise EndOfGenerator({OpCode.SEND : [fname, destination, error_action]})


@lexeme
@generate
def snapshot_command():
    """
    snapshot adam
    snapshot ws.parish
    """
    yield WHITESPACE
    yield snapshot
    target = yield context
    error_action = yield optional(on_error_clause, {OpCode.ONERROR: OpCode.RETRY})
    raise EndOfGenerator({OpCode.SNAPSHOT : {{OpCode.ON: target}, {error_action}}})


@lexeme
@generate
def log_command():
    """
    Log a message.
    """
    yield WHITESPACE
    yield lexeme(string('log'))
    text = yield quoted ^ everything
    raise EndOfGenerator({OpCode.LOG : {OpCode.LITERAL: text}})

###
# the STOP command is just "stop" or "quit"
###
stop_command = WHITESPACE >> lexeme(string('stop')).result(OpCode.STOP) ^ lexeme(string('quit')).result(OpCode.STOP)

###
# the NOP might be followed by anything else, or not. Effectively,
# it works as a comment in the object code for whatever might 
# come afterwards.
###
nop_command  = WHITESPACE >> lexeme(string('nop')).result(OpCode.NOP) + \
    optional(stop_command ^ log_command ^ send_command ^ exec_command ^ snapshot_command)

any_command = nop_command ^ stop_command ^ log_command ^ send_command ^ exec_command ^ snapshot_command
wslanguage = WHITESPACE >> any_command << optional(seq_pt)

@lexeme
@generate
def wsscript():
    """
    The traditional concept of the compound statement
    """
    yield WHITESPACE
    statements = yield many(sepBy(any_command, seq_pt))
    yield eof
    raise EndOfGenerator(statements)


@trap
def make_tree(opcodes:tuple) -> SloppyTree:
    """
    Run down the opcodes, and build a tree so that we can use the 
    usual tree functions to find things. The general format of a
    successfully parsed input is 
        - an opcode 
        - optionally followed by tuples
        - each interior tuple is an opcode and an operand
        - the operand may be a single or an iterable.
    """
    return opcodes
    
    ###
    # Make sure the argument is a tuple, even if it is a one-tuple.
    ###
    if not isinstance(opcodes, tuple):
        opcodes = (opcodes,)

    t = SloppyTree()

    ###
    # If we get an atomic opcode, create a tree that only has a root,
    # and we are done.
    ###
    command = opcodes[0]
    if not isinstance(command, Hashable): command=tuple(command)
    t[command]
    instructions = opcodes[1:]
    if not len(instructions): return t

    for action in instructions:
        opcode = action[0]
        if not isinstance(opcode, OpCode):
            raise Exception(f"Found {action}. Excepted a tuple or an OpCode")
        operands = action[1:]
        t[command][opcode] = operands

    return t


@trap
def squash_tuple(t:tuple) -> tuple:
    """
    Function to replace one-tuple values with the tuple element.
    """
    if not isinstance(t, tuple): return t

    new_t = []
    for _ in t:
        if isinstance(_, tuple) and len(_) == 1:
            new_t.append(_[0])
        else:
            new_t.append(_)

    return tuple(new_t)


@trap
def tuple_to_tree(tup:tuple) -> SloppyTree:
    """Recursively convert a nested tuple to a nested dictionary."""
    # Base case: if the input is not a tuple, return it directly
    if not isinstance(tup, tuple):
        return tup
    
    # If the tuple contains two elements and the first element is not a tuple,
    # it's a key-value pair to convert directly into a dictionary item
    if len(tup) == 2 and not isinstance(tup[0], tuple):
        return {tup[0]: tuple_to_dict(tup[1])}
    
    # Otherwise, recursively convert each item in the tuple into a dictionary
    return SloppyTree({k: tuple_to_dict(v) for k, v in tup})




@trap
def wscontrolparser_main(myargs:argparse.Namespace) -> int:
    """
    For testing. Pick a parser and a string and print the result or
    the error.
    """
    global parsertests
    print(f"Running {len(parsertests)} tests.")
    for k, v in parsertests:
        this_parser = globals()[k]
        print(f"\nParsing >>{v}<< with {k}\n")
        if use_resolver:
            pprint(resolver.resolver(tuple_to_tree(this_parser.parse(v))))
        else:
            pprint(tuple_to_tree(this_parser.parse(v)))

    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="wscontrolparser", 
        description="What wscontrolparser does, wscontrolparser does best.")

    parser.add_argument('-c', '--config', type=str, default="wscontrol.toml",
        help="Name of the toml file for configuration. Defaults to wscontrol.toml")

    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")

    parser.add_argument('-r', '--resolve', action='store_true',
        help="Invoke the resolver if this is set.")

    myargs = parser.parse_args()
    use_resolver = myargs.resolve

    config = wsconfig.WSConfig(myargs.config)

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

