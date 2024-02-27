export WSCONTROLHOME=$(find $HOME -name wscontrol -type d 2>/dev/null | head -1)
echo "WSCONTROLHOME is set to $WSCONTROLHOME"

function wscontrol
{
    command pushd $WSCONTROLHOME >/dev/null
    clear
    python wscontrol.py $@
    command popd >/dev/null
}

function parsertests
{
    command pushd $WSCONTROLHOME >/dev/null
    clear
    python wscontrolparser.py $@
    command popd >/dev/null
}

wscontrol $@
