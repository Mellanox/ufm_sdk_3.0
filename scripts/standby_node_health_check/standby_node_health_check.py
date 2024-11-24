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

import json
import re
import subprocess
import argparse
import sys
from typing import List


def parse_arguments():
    parser = argparse.ArgumentParser(description="Checking if standby node is ready.")

    parser.add_argument(
        "--fabric-interfaces",
        nargs="+",
        required=True,
        help="Specify one or more fabric interfaces (at least one is required), eg ib0, mlx3_0",
    )

    parser.add_argument(
        "--mgmt-interfaces",
        nargs="+",
        required=True,
        help="Specify one or more management interfaces (at least one is required), eg eth0, eth1",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args()
    return args


class StandbyNodeHealthChecker:
    UFM_HA_CLUSTER_COMMAND = "ufm_ha_cluster {}"
    SYSTEMCTL_IS_ACTIVE_COMMAND = "systemctl is-active {}.service"

    def __init__(self, fabric_interfaces, mgmt_interfaces):
        self._fabric_interfaces = fabric_interfaces
        self._mgmt_interfaces = mgmt_interfaces
        self._ufm_ha_status_string = ""

    @classmethod
    def _run_command(cls, command: str):
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                check=False,
            )
            return result.returncode, result.stdout.replace("\t", "").strip()
        except Exception as e:
            return -1, "", str(e)

    def _check_ib_interfaces(self):
        result = True
        ib_interfaces_status = self._run_and_parse_ibstat()
        ib_to_ml_map = self._get_ib_to_mlx_port_mapping()
        for ib_interface in self._fabric_interfaces:
            ib_interface_to_validate = ib_interface
            if not ib_interface.startswith("mlx"):
                ib_interface_to_validate = ib_to_ml_map.get(ib_interface, ib_interface)
            if ib_interface_to_validate not in ib_interfaces_status:
                print(f"{ib_interface} is not in the list of IB interfaces")
                result = False
            elif not self._check_ib_interface(
                ib_interface_to_validate, ib_interfaces_status
            ):
                print(
                    f"IB interface {ib_interface} is not active "
                    f"{ib_interfaces_status[ib_interface_to_validate]}"
                )
                result = False
        if result:
            print("All given IB interfaces are active")
        return result

    @classmethod
    def _get_ib_to_mlx_port_mapping(cls):
        ret_code, stdout = cls._run_command("ibdev2netdev")
        if ret_code != 0:
            print("Failed to run ibdev2netdev")
            return {}
        line_regex = re.compile(r"^([\w\d_]+) port \d ==> ([\w\d]+)")
        lines = stdout.splitlines()
        ib_to_mlx_map = {}
        for line in lines:
            cur_line_match = line_regex.match(line)
            if cur_line_match:
                mlx_port = cur_line_match.group(1)
                ib_port = cur_line_match.group(2)
                ib_to_mlx_map[ib_port] = mlx_port
        return ib_to_mlx_map

    @classmethod
    def _check_ib_interface(cls, ib_interface: str, ib_interfaces_status: dict):
        if ib_interface in ib_interfaces_status:
            ib_state = ib_interfaces_status[ib_interface]["State"]
            physical_state = ib_interfaces_status[ib_interface]["Physical_state"]
            if ib_state == "active" and physical_state == "linkup":
                return True
        return False

    @classmethod
    def _run_and_parse_ibstat(cls):
        retcode, stdout = cls._run_command("ibstat")
        if retcode != 0:
            print("Cannot run ibstat")
            return {}
        lines = stdout.splitlines()
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
                ca_info[current_ca]["Physical_state"] = (
                    line.split(":")[1].strip().lower()
                )

        return ca_info

    @classmethod
    def _run_and_parse_ip_link_show(cls):
        ret_code, ip_link_show_output = cls._run_command("ip --json link show")
        if ret_code != 0:
            print("Failed to run ip link show")
            return {}
        interfaces = cls._parse_ip_link_output(ip_link_show_output)
        return interfaces

    @classmethod
    def _parse_ip_link_output(cls, ip_link_output: str):
        interfaces = {}
        try:
            link_data = json.loads(ip_link_output)
            for entry in link_data:
                ifname = entry.get("ifname")
                operstate = entry.get("operstate", "").lower()  # Get state in lowercase
                link_type = entry.get("link_type", "").lower()

                if ifname and link_type == "ether":
                    interfaces[ifname] = operstate

        except json.JSONDecodeError:
            print("Error while parssing ib link show command")
        return interfaces

    def _check_eth_interfaces(self):
        interfaces_status = self._run_and_parse_ip_link_show()
        result = True
        for interface in self._mgmt_interfaces:
            if interface not in interfaces_status:
                print(f"{interface} is not in the list of management interfaces")
                result = False
            elif interfaces_status[interface] != "up":
                print(
                    f"Interface {interface} is not active {interfaces_status[interface]}"
                )
                result = False
        if result:
            print("All given ether interfaces are active")
        return result

    @classmethod
    def _check_if_ha_is_enabled(cls):
        command = cls.UFM_HA_CLUSTER_COMMAND.format("is-ha")
        ret_code, stdout = cls._run_command(command)
        if ret_code != 0 or stdout.lower() != "yes":
            print("HA is not enabled")
            return False
        print("HA is enabled")
        return True

    def run_basic_checks(self):
        result = True
        checks = [
            self._check_ib_interfaces,
            self._check_eth_interfaces,
            self._check_if_ha_is_enabled,
        ]
        for check in checks:
            if not check():
                result = False
        return result

    @classmethod
    def check_if_standby_node(cls):
        command = cls.UFM_HA_CLUSTER_COMMAND.format("is-master")
        _, stdout = cls._run_command(command)
        # Not checking the ret code since it is 1 when running on the standby node
        if stdout != "standby":
            print(f"Not a standby node but {stdout}")
            return False
        print("On standby node")
        return True

    @classmethod
    def _check_pcs_status(cls):
        command = "pcs status"
        return_code, _ = cls._run_command(command)
        if return_code != 0:
            print(f"pcs status is not ok, return code is {return_code}")
            return False
        print("PCS status is OK")
        return True

    @classmethod
    def _check_corosync_rings_status(cls):
        ret_code, corosync_output = cls._run_command("corosync-cfgtool -s")
        if ret_code != 0:
            print("Failed to run corosync-cfgtool -s")
            return {}
        corosync_output_lines = corosync_output.splitlines()
        rings_statuses = cls._parse_corsync_rings_old_output(corosync_output_lines)
        if not rings_statuses:
            print("From new")
            rings_statuses = cls._parse_corsync_rings_new_output(corosync_output_lines)
        print(f"RING RES {rings_statuses}")
        if not rings_statuses:
            print("Could not find any corosync rings status")
            return False
        result = True
        try:
            for ring in rings_statuses:
                if not rings_statuses[ring]["status_check"]:
                    text = rings_statuses[ring]["status_text"]
                    if text:
                        print(f"{ring} is not OK - {text}")
                    else:
                        print(f"{ring} has an empty status")
                    result = False
        except Exception as e:
            print(f"Failed to parse corosync rings status: {e}")
            return False
        if result:
            print("All rings are OK")
        return result

    @classmethod
    def _parse_corsync_rings_old_output(clsm, corosync_output_lines: List[str]):
        # This function handles the old ouptut of corsync, for example:
        # Printing ring status.
        # Local node ID 2
        # RING ID 0
        # 	id	= 11.0.0.11
        # 	status	= ring 0 active with no faults
        # RING ID 1
        # 	id	= 10.209.44.110
        # 	status	= ring 1 active with no faults
        rings_info = {}
        ring_id_regex = re.compile(r"^RING ID (\d+)")
        id_ip_regex = re.compile(r"id\ *= ([\d\.]+)")
        status_regex = re.compile(r"^status:\s*(.*)$")
        current_ring = None
        current_ip = None
        for line in corosync_output_lines:
            ring_match = ring_id_regex.match(line)
            if ring_match:
                current_ring = ring_match.group(1)
            ring_ip = id_ip_regex.match(line)
            if ring_ip:
                current_ip = ring_ip.group(1)
            old_status_match = status_regex.match(line)
            print(
                f"current ring {current_ring} current ip {current_ring} old status {old_status_match} line {line}"
            )
            if current_ring and current_ip and old_status_match is not None:
                status_text = old_status_match.group(1)
                status_check = "active with no faults" in status_text
                rings_info[f"Ring {current_ring}"] = {
                    "ip": current_ip,
                    "status_text": status_text,
                    "status_check": status_check,
                }
                current_ring = current_ip = None
        return rings_info

    @classmethod
    def _parse_corsync_rings_new_output(cls, corosync_output_lines: List[str]):
        # This function handles the new output of corsync, for example:
        # Printing link status.
        # Local node ID 1
        # LINK ID 0
        # 	addr	= 1.1.36.7
        # 	status:
        # 		node 0:	link enabled:1	link connected:1
        # 		node 1:	link enabled:1	link connected:1
        # LINK ID 1
        # 	addr	= 10.209.226.31
        # 	status:
        # 		node 0:	link enabled:0	link connected:1
        # 		node 1:	link enabled:1	link connected:1
        rings_info = {}
        ring_id_regex = re.compile(r"^LINK ID (\d+)")
        id_ip_regex = re.compile(r"addr\ *= ([\d\.]+)")
        node_status_regex = re.compile(
            r"^node (\d+):link enabled:(\d)link connected:(\d)"
        )
        current_ring = None
        current_ip = None
        for line in corosync_output_lines:
            ring_match = ring_id_regex.match(line)
            if ring_match:
                current_ring = ring_match.group(1)
            ring_ip = id_ip_regex.match(line)
            if ring_ip:
                current_ip = ring_ip.group(1)
            new_status_match = node_status_regex.match(line)
            if current_ring and current_ip and new_status_match:
                node_id = new_status_match.group(1)
                link_enabled = new_status_match.group(2)
                link_connected = new_status_match.group(3)
                status_check = link_enabled == "1" and link_connected == "1"
                rings_info[f"Link {current_ring} Node {node_id}"] = {
                    "ip": current_ip,
                    "status_text": f"node {node_id} link enabled:{link_enabled} link connected:{link_connected}",
                    "status_check": status_check,
                }
        return rings_info

    @classmethod
    def check_if_service_is_active(cls, service_name: str):
        """
        service_name for example : pacemaker
        """
        command = cls.SYSTEMCTL_IS_ACTIVE_COMMAND.format(service_name)
        _, stdout = cls._run_command(command)
        if stdout == "active":
            print(f"Service {service_name} is active")
            return True
        print(f"Service {service_name} is not active")
        return False

    def set_ufm_ha_cluster_status_string(self):
        command = self.UFM_HA_CLUSTER_COMMAND.format("status")
        ret_code, res_string = self._run_command(command)
        if ret_code != 0:
            print("Failed to get ha cluster status")
            res_string = ""
        self._ufm_ha_status_string = res_string

    def _get_status_value_from_ha_cluster_status(self, keyword: str):
        for line in self._ufm_ha_status_string.splitlines():
            line = line.strip()
            if line.startswith(keyword):
                val = line.split(":", 1)[-1].strip().lower()
                val = (
                    val.replace("[", "")
                    .replace("]", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                return val
        return None

    def check_drbd_connectivity(self):
        if not self._ufm_ha_status_string:
            return False
        drbd_connectivity_status = self._get_status_value_from_ha_cluster_status(
            "DRBD_CONNECTIVITY"
        )
        if drbd_connectivity_status != "connected":
            print(
                f"DRBD CONNECTIVITY status is {drbd_connectivity_status} and not Connected"
            )
            return False
        print("DRBD CONNECTIVITY status is ok - Connected")
        return True

    def check_drdb_role(self):
        if not self._ufm_ha_status_string:
            return False
        drdb_resource_status = self._get_status_value_from_ha_cluster_status(
            "DRBD_ROLE"
        )
        if drdb_resource_status != "secondary":
            print(f"DRDB ROLE status is {drdb_resource_status} and not Secondary")
            return False
        print("DRDB ROLE status is ok - Secondary")
        return True

    def check_drbd_disk_state(self):
        if not self._ufm_ha_status_string:
            return False
        drbd_disk_state = self._get_status_value_from_ha_cluster_status("DISK_STATE")
        if drbd_disk_state != "uptodate":
            print(f"DRBD DISK STATE status is {drbd_disk_state} and not UpToDate")
            return False
        print("DRBD DISK STATE status is ok - UpToDate")
        return True

    def run_advanced_checks(self):
        result = True
        self.set_ufm_ha_cluster_status_string()
        checks = [
            self._check_pcs_status,
            # On comment, there is an instability here between versions
            # self._check_corosync_rings_status,
            self.check_drdb_role,
            self.check_drbd_connectivity,
            self.check_drbd_disk_state,
        ]
        for check in checks:
            if not check():
                result = False
        check_with_arg = [
            (self.check_if_service_is_active, "corosync"),
            (self.check_if_service_is_active, "pacemaker"),
            (self.check_if_service_is_active, "pcsd"),
        ]
        for check, arg in check_with_arg:
            if not check(arg):
                result = False
        return result


def main(args):
    standby_node_checker = StandbyNodeHealthChecker(
        args.fabric_interfaces, args.mgmt_interfaces
    )
    if not standby_node_checker.run_basic_checks():
        print("Due to previous failures, stopping the test")
        # sys.exit(1)

    if not standby_node_checker.check_if_standby_node():
        print("The tool should only be run on Standby node")
        # sys.exit(1)

    if not standby_node_checker.run_advanced_checks():
        sys.exit(1)
    print("All checks passed")


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
