# UFM node health check

## What
This script is meant to help a UFM HA user, to make sure that his master or standby node is configured correctly and ready.

## How to run
1. Using python 3.6 and above.
2. No prerequisites are needed.
3. The script is meant to run on a master or standby node only.
4. Place the script in a directory, for example under `/tmp`.
5. Run the command `python3 standby_node_health_check --fabric-interfaces ib0 ib1 --mgmt-interface ens192`

## What the script is checking
1. checking if all given fabric interfaces are up.
2. Checking if all given management interface are up.
3. Checking ufm ha is configured.
5. Checking if the node is master or a standby.
6. Checking Pacemaker status.
7. Checking corosync service is active.
8. Checking pacemaker service is active.
9. Checking pcsd service is active.
10. Checking the DRBD role is primary or Secondary (depending if we are on master ot standby).
11. DRBD connectivity state is Connected.
12. DRBD disk state is UpToDate.
13. If any of the previous tests fails, stop and set the return code is 1.

Note - In case that all tests have passed, the return code is 0.

## Logging
The script output all its logs to the screen. 
They user can change the log level, during run time by passing the `--log-level` parameter.
The default log level is `INFO`.

In addition, all the warnings and errors are also send to the local syslog.
