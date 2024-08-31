#!/bin/bash
#This script allows run UFM simulator

GetOpts() {
	while getopts :s: op; do
		case "$op" in
			s) export SIMULATION_FILE="$OPTARG"
				;;
			*) usage;;
		esac
		opt="$opt $op"
	done
}

usage () {
	echo -e "	$basename -s <simulation file> "
	exit 1
}


COMMON=/opt/ufm/scripts/common
test ! -f $COMMON && echo "missing $COMMON" && exit 1
. $COMMON
basename=`basename $0`

GetOpts $*
test -z "$SIMULATION_FILE" && usage

is_ha=`isHA`
if [ "$is_ha" == "yes" ];then
    /etc/init.d/ufmha stop
    hamode=hamode
elif [ -f $IS_APPLIANCE_INDICATOR ]; then
    /etc/init.d/ufmd stop
    hamode=""
else
    systemctl stop ufm-enterprise
    hamode=""
fi
#run ibsim
export LD_LIBRARY_PATH=/opt/ufm/opensm/lib/
nohup  /opt/ufm/opensm/bin/ibsim -S 100000 -P 500000 -N 100000 -s $SIMULATION_FILE &
export LD_PRELOAD=/opt/ufm/opensm/lib/umad2sim/libumad2sim.so
export SIM_HOST=`grep "H-0c"  $SIMULATION_FILE | grep Ca | tail  -1 | awk -F' ' '{print $3}' | tr -d '\"#'`
if [ -z "$SIM_HOST" ];then
	echo "Failed define SIM_HOST value"
	exit 1
fi

echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH}"
echo "LD_PRELOAD=${LD_PRELOAD}"
echo "SIM_HOST=${SIM_HOST}"

status=0
/etc/init.d/ufmd $hamode simstart > /dev/null || status=$((status + 1 ))
/etc/init.d/ufmd $hamode mhrestart_without_health > /dev/null || status=$((status + 1 ))
/etc/init.d/ufmd $hamode health_stop > /dev/null || status=$((status + 1 ))
/etc/init.d/ufmd $hamode ufmprd_start > /dev/null || status=$((status + 1 ))
/opt/ufm/opensm/sbin/ibpm -t 50 -m 5 -c /opt/ufm/data/records.conf -n 40000 -l /opt/ufm/files/log/ibpm.log || status=$((status + 1 ))
exit $status
