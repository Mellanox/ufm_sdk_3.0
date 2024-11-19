#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import re
import subprocess
import argparse
import sys
from typing import List


UFM_HA_CLUSTER_COMMAND = "ufm_ha_cluster {}"
SYSTEMCTL_IS_ACTIVE_COMMAND = "systemctl is-active {}.service"


####################################################
#### All the functions below are helper function
def _run_command(command: str):
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def _run_and_parse_ibstat():
    retcode, stdout, _ = _run_command("ibstat")
    if retcode != 0:
        print("Cannot run ibstat")
        return {}
    lines = stdout.split("\n")
    ca_info = {}
    current_ca = None

    for line in lines:
        line = line.strip()
        if line.startswith("CA '"):
            current_ca = line.split("'")[1]
            ca_info[current_ca] = {}
        elif current_ca and line.startswith("State:"):
            ca_info[current_ca]["State"] = line.split(":")[1].strip().lower()
        elif current_ca and line.startswith("Physical state:"):
            ca_info[current_ca]["Physical_state"] = line.split(":")[1].strip().lower()

    return ca_info


def _check_ib_interface(ib_interface: str, ib_interfaces_status: dict):
    if ib_interface in ib_interfaces_status:
        ib_state = ib_interfaces_status[ib_interface]["State"]
        physical_state = ib_interfaces_status[ib_interface]["Physical_state"]
        if ib_state == "active" and physical_state == "linkup":
            return True
    return False


def _parse_ip_link_output(ip_link_output: str):
    interface_regex = re.compile(r"^(\d+): (\S+):.*state (\S+) .*")
    link_regex = re.compile(r"^\s+link/(\S+)")

    interfaces = {}
    lines = ip_link_output.splitlines()
    current_interface = None
    state = None

    for line in lines:
        interface_match = interface_regex.match(line)
        if interface_match:
            current_interface = interface_match.group(2)
            state = interface_match.group(3)
        else:
            link_match = link_regex.match(line)
            if link_match and current_interface:
                link_type = link_match.group(1)
                if link_type == "ether" and not current_interface.startswith("docker"):
                    interfaces[current_interface] = state.lower()

    return interfaces


def _run_and_parse_ip_link_show():
    ret_code, ip_link_show_output, _ = _run_command("ip link show")
    if ret_code != 0:
        print("Failed to run ip link show")
        return {}
    interfaces = _parse_ip_link_output(ip_link_show_output)
    return interfaces


def _run_and_parse_corosync_rings():
    ret_code, corosync_output, _ = _run_command("corosync-cfgtool -s")
    if ret_code != 0:
        print("Failed to run corosync-cfgtool -s")
        return {}

    rings_info = {}
    lines = corosync_output.splitlines()
    current_ring = None

    ring_id_regex = re.compile(r"^RING ID (\d+)")
    status_regex = re.compile(r"^\s+id\s+= (\S+)\s+status\s+= (.+)")

    for line in lines:
        ring_match = ring_id_regex.match(line)
        if ring_match:
            current_ring = ring_match.group(1)

        status_match = status_regex.match(line)
        if status_match and current_ring is not None:
            ip_address = status_match.group(1)
            status_text = status_match.group(2)
            status_check = "active with no faults" in status_text
            rings_info[current_ring] = {
                "ip": ip_address,
                "status_text": status_text,
                "status_check": status_check,
            }

    return rings_info


def _get_status_value_from_ha_cluster_status(command_output: str, keyword: str):
    for line in command_output.splitlines():
        line = line.strip()
        if line.startswith(keyword):
            return line.split(":", 1)[-1].strip().lower()
    return None


#############################################################
# This are the "main" functions


def check_ib_interfaces(ib_interfaces: List[str]):
    result = True
    ib_interfaces_status = _run_and_parse_ibstat()
    for ib_interface in ib_interfaces:
        if not ib_interface in ib_interfaces_status:
            print(f"{ib_interface} is not in the list of IB interfaces")
            result = False
        elif not _check_ib_interface(ib_interface, ib_interfaces_status):
            print(f"IB interface {ib_interface} is not active {ib_interfaces_status[ib_interface]}")
            result = False
    if result:
        print("All given IB interfaces are active")
    return result


def check_eth_interfaces(eth_interfaces: List[str]):
    interfaces_status = _run_and_parse_ip_link_show()
    result = True
    for interface in eth_interfaces:
        if not interface in interfaces_status:
            print(f"{interface} is not in the list of ether interfaces")
            result = False
        elif interfaces_status[interface] != "up":
            print(f"Interface {interface} is not active {interfaces_status[interface]}")
            result = False
    if result:
        print("All given ether interfaces are active")
    return result


def check_if_ha_is_enabled():
    command = UFM_HA_CLUSTER_COMMAND.format("is-ha")
    ret_code, stdout, _ = _run_command(command)
    if ret_code != 0 or not (stdout.lower() == "yes"):
        print("HA is not enabled")
        return False
    print("HA is enabled")
    return True


def check_pcs_status():
    command = "pcs status"
    return_code, _, _ = _run_command(command)
    if return_code != 0:
        print("pcs status is not ok, return code is {return_code}")
        return False
    print("PCS status is OK")
    return True


def check_corosync_rings_status():
    rings_statuses = _run_and_parse_corosync_rings()
    if not rings_statuses:
        print("Could not find any rings")
        return False
    result = True
    for ring in rings_statuses:
        if not rings_statuses[ring]["status_check"]:
            text = rings_statuses[ring]["status_text"]
            print(f"Ring {ring} is {text}")
            result = False
    print("All rings are OK")
    return result


def check_if_service_is_active(service_name: str):
    """
    service_name for example : pacemaker
    """
    command = SYSTEMCTL_IS_ACTIVE_COMMAND.format(service_name)
    _, stdout, _ = _run_command(command)
    if stdout == "active":
        return True
    else:
        return False


def get_ufm_ha_cluster_status_string():
    command = UFM_HA_CLUSTER_COMMAND.format("status")
    ret_code, stdout, _ = _run_command(command)
    if ret_code != 0:
        print("Failed to get ha cluster status")
        return ""
    return stdout


def check_drdb_resource(cluster_status: str):
    if not cluster_status:
        return False
    drdb_resource_status = _get_status_value_from_ha_cluster_status(
        cluster_status, "DRBD_RESOURCE"
    )
    if drdb_resource_status != "ha_data":
        print(f"DRDB RESOURCE status is {drdb_resource_status} and not ha_data")
        return False
    return True


def check_drbd_connectivity(cluster_status: str):
    if not cluster_status:
        return False
    drbd_connectivity_status = _get_status_value_from_ha_cluster_status(
        cluster_status, "DRBD_CONNECTIVITY"
    )
    if drbd_connectivity_status != "connected":
        print(
            f"DRBD CONNECTIVITY status is {drbd_connectivity_status} and not Connected"
        )
        return False
    return True


def check_drbd_disk_state(cluster_status: str):
    if not cluster_status:
        return False
    drbd_disk_state = _get_status_value_from_ha_cluster_status(
        cluster_status, "DISK_STATE"
    )
    if drbd_disk_state != "uptodate":
        print(f"DRBD DISK STATE status is {drbd_disk_state} and not UpToDate")
        return False
    return True

def get_is_standby_node():
    command = UFM_HA_CLUSTER_COMMAND.format("is-master")
    _, stdout, _ = _run_command(command)
    #Not checking the ret code since it is 1 when running on the standby node
    if stdout != "standby":
        print(f"Not a standby node but {stdout}")
        return False
    print("On standby node")
    return True

def parse_arguments():
    parser = argparse.ArgumentParser(description="Checking if standby node is ready.")

    parser.add_argument(
        "--fabric-interfaces",
        nargs="+",
        required=True,
        help="Specify one or more fabric interfaces (at least one is required)"
    )

    parser.add_argument(
        "--mngmnt-interfaces",
        nargs="+",
        required=True,
        help="Specify one or more management interfaces (at least one is required)"
    )

    args = parser.parse_args()
    return args


def main(args):
    ib_interfaces_status = check_ib_interfaces(args.fabric_interfaces)
    #TODO Handle when the input is ib and not ml
    eth_interfaces_status = check_eth_interfaces(args.mngmnt_interfaces)
    is_ha_enabled = check_if_ha_is_enabled()
    if not all([ib_interfaces_status, eth_interfaces_status, is_ha_enabled]):
        print("Due to previous failures, stopping the test")
        sys.exit(1)
    is_standby_node = get_is_standby_node()
    pacemaker_status = check_pcs_status()
    # corosync_rings_status = check_corosync_rings_status()
    # corosync_service_stats = check_if_service_is_active("corosync")
    # pacemaker_service_status = check_if_service_is_active("pacemaker")
    # pcsd_service_status = check_if_service_is_active("pcsd")

    # ha_cluster_status_string = get_ufm_ha_cluster_status_string()
    # drdb_resures_status = check_drdb_resource(ha_cluster_status_string)
    # drdb_connectivty_status = check_drbd_connectivity(ha_cluster_status_string)
    # drdb_disk_usage_status = check_drbd_disk_state(ha_cluster_status_string)
    # if not all(
    #     [
    #         pacemaker_status,
    #         corosync_rings_status,
    #         corosync_service_stats,
    #         pacemaker_service_status,
    #         pcsd_service_status,
    #         drdb_resures_status,
    #         drdb_connectivty_status,
    #         drdb_disk_usage_status,
    #     ]
    # ):
    #     sys.exit(1)


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
