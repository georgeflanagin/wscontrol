# -*- coding: utf-8 -*-
import typing
from   typing import *

min_py = (3, 6)

###
# Standard imports, starting with os and sys
###
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)


LOGO=R"""

                                          .
                                         o
                                       ---
                   .........           | |
                 .'------.' |          |o|
                | .-----. | |         .' '.
                | |  U  | | |        /  o  \
              __| |  R  | | |;. ____:~~~~o~~:__
             /  |*`-----'.|.' `;    '._____.' //
            /   `---------' .;'   Linux      //
           /  .''''////////;'   Workstation //
          /  / ######### /;/  Control      //|
         /  / ######### //                //||
        /   `-----------'   Version 0.1  // ||
       /________________________________//| ||
       `--------------------------------' | ||
          | ||      | ||         | ||     | ||
          | ||      `""'         | ||     `""'
          | ||                   | ||
          | ||                   | ||
          | ||                   | ||
          `""'                   `""'
     
"""
