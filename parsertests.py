# -*- coding: utf-8 -*-
"""
Sample statements in the parser language. Append as required
as the language evolves.
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
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2024, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'

# The key is the name of the parser that you want to test,
# and the value is a string representing the action.
parsertests = (
    # parse a keyword with varying amounts of space around it.
    #("wslanguage",  'stop'),
    #("wslanguage",  '  stop   '),
    #("wslanguage",  '  stop'),
    #("hostname",  "adam" ),
    #("hostname",  "adam " ),
    #("hostnames",  "(adam, anna)"),
    #("context",  "(adam, anna, michael)"),
    #("context",  "michael"),
    #("context",  "(michael)"),

    # ("on_error_clause", "on_error ignore"),

    # ("wslanguage", "send kevin to kevin on_error ignore"),

    # one file to multiple hosts.
    # ("wslanguage",  "send /ab/c/d to (adam, anna, kevin)"),
    # multiple files to multiple hosts.
    ("wslanguage",  "send (/ab/c/d, $HOME/.bashrc) to (adam, anna, kevin)"),

    # one command on a configured group.
    # ("wslanguage",  'on ws.parish do "date -%s"'),
    # one command on specific hosts.
    ("wslanguage",  'on (billieholiday, badenpowell) do "date -%s"'),

    # These are tests on the full language.
    # ("wslanguage",  'on (sarah, evan, kevin) do "cat /etc/fstab"'),   
    ("wslanguage",  """on (billieholiday,  adam, thais) do (
                "tail -1 /etc/fstab", 
                "sed -i 's/141.166.88.99/newhost/' somefile"
                )"""),

    # ("wslanguage",  """on adam do from x.sh"""),
    # ("wslanguage",  """on adam do from local ~/X.sh"""),

    # ("wslanguage",  """log "hello world" """),
    # ("wslanguage",  """snapshot erica """),
    # ("wslanguage",  """snapshot (erica, evan) """),
    # ("wslanguage",  """snapshot ws.parish """),
    ("wslanguage",  """stop"""),
    )



