# Stand by node health check

## What
This script is meant to help a UFM HA user, to make sure that his standby server is configured correctly and ready to become the new Master, in case of failover.

## How to run
1. Using python 3.6 and above
2. No prequesition are needed
3. The script is meant to run on a standby node only.
4. Place the script in a directory, for example under `/tmp`
5. Run the command `python3 standby_node_health_check --fabric-interfaces ib0 ib1 --mgmt-interface ens192`

## What the script is checking
1. checking if all given fabric interfaces are up.
2. Checking if all given management interface are up.
3. Checking ufm ha is configured.
5. Checking if the node is a standby.
6. Checking Pacemaker status.
7. Checking corosync service is active.
8. Checking pacemaker service is active.
9. Checking pcsd service is active.
10. Checking the DRBD role is Secondary.
11. DRBD connectivity state is Connected.
12. DRBD disk state is UpToDate.
13. If any of the previous tests fails, stop and set the return code is 1.

Note - In case that all tests have passed, the return code is 0.
