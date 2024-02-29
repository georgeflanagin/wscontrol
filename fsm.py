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
from   collections.abc import Iterable
import contextlib
import getpass
mynetid = getpass.getuser()
import logging
import re
import socket
this_host = socket.gethostname()

###
# Installed libraries.
###


###
# From hpclib
###
from   dorunrun import dorunrun
import linuxutils
from   sloppytree import SloppyTree
from   sloppytree import *
import sqlitedb
from   urdecorators import trap
import urlogger

###
# imports and objects that are a part of this project
###
from opcodes import OpCode
from wsview import * #utility for a snapshot
from wscontrolparser import *
from parsertests import parsertests
###
# Global objects and initializations
###
logger = urlogger.URLogger(logfile='wscontrol.log', level=logging.DEBUG)
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



class FSM:
    SQL = """INSERT INTO master (who, host, command, result) VALUES (?, ?, ?, ?)"""
    pattern = re.compile(r'@([^ ]*) ') 

    @trap
    def __init__(self, program:SloppyTree, db:sqlitedb.SQLiteDB) -> int:
        """
        Interpret the OpCodes in program, and return a Linux compatible
        status code.
        """
        self.program = program
        self.db = db
        
        self.jump_table = {
            OpCode.EXEC : self._execute,
            OpCode.SEND : self._send,
            OpCode.SNAPSHOT : self._snapshot,
            OpCode.STOP : self._stop,
            OpCode.NOP : self._nop, 
            }

        # k will be something like OpCode.EXEC or OpCode.SEND, and
        # the v will have the rest of the information.
        for k, v in program.items():
            result = self.jump_table[k](v)


    def _record_event(self, command:str, result:int) -> int:
        host = re.findall(FSM.pattern, command).pop()
        try:
            rowcount = self.db.execute_SQL(SQL, mynetid, host, command, result)
            return os.EX_OK if rowcount == 1 else rowcount
        except Exception as e:
            logger.error(f"Error recording event: {e}")
            return os.EX_IOERR


    @staticmethod
    def squish_spaces(s:str) -> str:
        return re.sub(r'\s+', ' ', s).strip()

                        
    def _action(self) -> str:
        return self.program[OpCode.ACTION] 

    def _context(self) -> list:
        return self.program[OpCode.CONTEXT]

    def _do_it(connection:str, action:str) -> SloppyTree:
        command = ' '.join((connection, action))
        result = SloppyTree(dorunrun(command, return_datatype=dict))
        return result
        

    def _execute(self) -> int:
        """
        Let's *do* something on a host.
        """
        connections = self._on(program[OpCode.ON])
        actions = self._do(program[OpCode.DO])
        for connection in connections:
            for action in actions:
                result = self._do_it(connection, action) 
                self.record_event(' '.join((connection, action)), result.code)
                if not result.OK:
                    self.jump_table[result]()

        return 0


    def _host(p:SloppyTree) -> str:
        return self.squish_spaces(f"""
            ssh -o ConnectTimeout {p.connecttimeout}
            {p.user}@{p.hostname}:{p.port}
            """)

    def snapshot(p:SloppyTree) -> int:
        
        print("//", fsm_util(), "//")
        global parsertests
        for k, v in parsertests:
            print(k, v)
            this_parser = globals()[k]
            p = resolver.resolver(this_parser.parse(v))
        return p
        ''' 
        
        hostnames = []
        for host in p.SNAPSHOT.CONTEXT:
            hostnames.append(SNAPSHOT.CONTEXT.HOST)

        fork_ssh(hostnames)
        wrapper(display_data)
    
        return os.EX_OK
        '''
