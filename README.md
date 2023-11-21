# wscontrol
Python program to remotely control a collection of Linux workstations.

Many of us in HPC and other Academic Research Computing groups deal
with an environment that is just as bare bones on the administrative
side as it is on the calculation side.  This program is intended
to be operable with a minimum of constraints.  At University of
Richmond each member of the academic research environment is likely
to have a private workstation that is not often used for calculations,
but is a Linux computer connected to the same network as the research
computers. It is in this environment that we execute `wscontrol`,
or _workstation control_.

The one program, `wscontrol`, can be operated interactively. When used
this way, one can issue the same command to one, some, or all of the
computers that are under its administration. `wscontrol` can also be
used in a scripted, automated way, and these scripts can be saved for
later and repeated use.

Of primary importance, `wscontrol` keeps a record of what commands
have been issued, for which workstations, when this command was issued
and by whom. The usefulness should be clear: it helps with auditing, 
undo-ing mistakes, and redo-ing successes. 


## Configuration File

Everything about the environment can be placed in a single TOML file. 

## wscontrol Language

The language is designed to be human readable and writeable, and it 
makes it easy to do the most common things. Rather than provide the
entire EBNF grammar --- interested readers can examine the code in
`wscontrolparser.py` --- a few examples may suffice for most users. 

