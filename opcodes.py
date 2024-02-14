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

from   enum import IntEnum

class OpCode(IntEnum):
    OK          = 0

    # Actions to take if there are problems.
    IGNORE      = 8
    FAIL        = 9
    NEXT        = 10
    RETRY       = 11

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
    

    # Typing info for data
    HOST        = 64
    FILE        = 65
    ACTION      = 66
    
    # Atomic instructions that can appear anywhere. The
    # NOP instruction can replace any of the others, effectively
    # commenting out a portion of the code.
    LOG         = 124
    STOP        = 125
    NOP         = 126
    ERROR       = 127

