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

## Basic operation

Begin by sourcing `wscontrol.sh`. This file contains a few shell functions
that will make operation easier and less subject to errors. It also defines
`WSCONTROLHOME`, an environment variable that represents the default
location for the toml configuration file, the database, and the logfile.

`wscontrol` -- brings up the interactive console. The program will wait
for your next command until you type one of _exit_, _quit_, or _stop_.

`wscontrol << commandfile` -- will run the program as if you had typed
in everything in the `commandfile`. The program will echo the contents
of the `commandfile` to `stdout` while it processes your requests.

There are several command line switches.

`--config` -- Allows you to specify a config file other than `wscontrol.toml`
in the current directory.

`--db` -- Allows you to specify a database for recording the activity
if you want to use something other than the file named `wscontrol.db`
in the current directory.


`--loglevel` -- sets the threshold for logging messages. The default
is the system setting, `logging.INFO`.

`-z` -- will clear the logfile before starting.

## Configuration File

Everything about the environment can be placed in a single TOML file. 
By default, this is `wscontrol.toml`. `wscontrol` considers the TOML file
to be the highest authority for information about the workstations, and
all symbols are first checked to see if they have a definition in this file.

Given that `ssh` is the assumed communication channel between `wscontrol`
and the workstations in its pale, information from `~/.ssh/config` is 
also used, although information in `wscontrol.toml` takes precedence.

## wscontrol Language

**NOTE:** `wscontrol` has a shell escape that is provided by starting
any command with an exclamation point (`!`). The entire line is sent
to a shell process that is a child of `wscontrol`, running with the
permissions of the current user.

The language is designed to be human readable and writeable, and it 
makes it easy to do the most common things. Rather than provide the
entire EBNF grammar --- interested readers can examine the code in
`wscontrolparser.py` --- a few examples may suffice for most users. 

The language is as small as possible, and the parsing is entirely contained
in the source code file, `wscontrolparser.py`. The following is an 
approximate grammar for it, leaving out the most trivial definitions:

`hostname` -- string of alpha, underscore, and the dot.

`hostnames` -- One or more `hostname` elements, enclosed in parens,
and separated by commas.

`filename` -- string of alphanumeric, underscore, dash, dot, 
dollar sign, star, tilde, and plus. This definition allows for
the use of wildcard file names and environment variables, and `wscontrol`
does allow them and expand them. Note that a filename should not be
quoted, and the implication is that they do not have embedded spaces.

`filenames` -- One or more `filename` elements, enclosed in parens, and
separated by commas. 

`context := hostnames | hostname`

`op` -- a quoted string that represents something to "do."

`op_sequence` -- One or more `op` elements, enclosed in parens, and 
separated by commas.

`from_file_clause := from + filename` -- represents `op` elements to
be read from a file.

`do_clause := "do"  [op_sequence | op]`

`exec_command := context do_clause`

`send_command := "send" [filenames | filename] "to" context`

`log_command := "log" characters-until-EOL` 




