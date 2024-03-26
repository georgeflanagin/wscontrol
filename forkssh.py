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
import getpass
import logging
import fcntl
mynetid = getpass.getuser()

###
# From hpclib
###
import linuxutils
from   urdecorators import trap
import urlogger
from dorunrun import dorunrun
###
# imports and objects that are a part of this project
###
verbose = False

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2022, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'


@trap 
def get_hostname(ws:str):
    """
    Retrieves a hostname.
    """
    cmd = f"ssh -o ConnectTimeout=5 {ws} hostname"
    result = dorunrun(cmd, return_datatype = str)
    return result

@trap
def fork_ssh(list_of_hosts:list, function: object) -> None:
    '''
    Arguments: list oh hosts, function that gets information for each host.
                                function needs to take host as a parameter.

    Multiprocesses to ssh to each workstation and retrieve information 
    in parallel, significantly speeding up the process.
    '''
    DAT_FILE = os.path.join(os.getcwd(), 'info.dat')
    logger   = urlogger.URLogger(level=logging.INFO)
    
    try:
        os.unlink(DAT_FILE)
    except FileNotFoundError as e:
        # This is OK; the file has already been deleted.
        pass

    except Exception as e:
        # This is something else, let's find out what happened.
        logger.error(urlogger.piddly(f"Cannot continue. Unable to clear {DAT_FILE} because {e}."))
        sys.exit(os.EX_IOERR)

    pids = set()

    for ws in list_of_hosts:            

        # Parent process records the child's PID.
        if (pid := os.fork()):
            pids.add(pid)
            continue

        with open(DAT_FILE, 'a+') as infodat:
            try:
                # get the data for each workstation   
                data = function(ws)

                # each child process locks, writes to and unlocks the file
                fcntl.lockf(infodat, fcntl.LOCK_EX)
                infodat.write(f'{ws} {data}\n')
                infodat.close()
                
            except Exception as e:
                logger.error(urlogger.piddly(f"query of {ws} failed. {e}"))
                pass

            finally:
                logger.info(urlogger.piddly(f"{ws} {data}"))
                os._exit(os.EX_OK)

    # make sure all the child processes finished before the function 
    # returns.
    while pids:
        # The zero in the argument means we wait for any child.
        # The resulting pid is the child that sent us a SIGCHLD.
        pid, exit_code, _ = os.wait3(0) 
        pids.remove(pid)



@trap
def forkssh_main(myargs:argparse.Namespace) -> int:
    fork_ssh(["anna", "boyi", "adam", "irene"], get_hostname)

    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="forkssh", 
        description="What forkssh does, forkssh does best.")

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

