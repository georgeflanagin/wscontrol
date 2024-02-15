function wscontrol
{
    export WSCONTROL_HOME=$(find $HOME -name wscontrol -type d 2>/dev/null)
    command pushd $WSCONTROL_HOME >/dev/null
    python wscontrol.py $@
    command popd >/dev/null
}

function parsertests
{
    export WSCONTROL_HOME=$(find $HOME -name wscontrol -type d 2>/dev/null)
    command pushd $WSCONTROL_HOME >/dev/null
    python wscontrolparser.py $@
    command popd >/dev/null
}

wscontrol $@
