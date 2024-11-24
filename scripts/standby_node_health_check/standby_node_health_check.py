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


UFM_HA_CLUSTER_COMMAND = "ufm_ha_cluster {}"
SYSTEMCTL_IS_ACTIVE_COMMAND = "systemctl is-active {}.service"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Checking if standby node is ready.")

    parser.add_argument(
        "--fabric-interfaces",
        nargs="+",
        required=True,
        help="Specify one or more fabric interfaces (at least one is required)",
    )

    parser.add_argument(
        "--mngmnt-interfaces",
        nargs="+",
        required=True,
        help="Specify one or more management interfaces (at least one is required)",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args()
    return args


class StandbyNodeHealthChecker:
    def __init__(self, fabric_interfaces, mngmnt_interfaces):
        self._fabric_interfaces = fabric_interfaces
        self._mngmnt_interfaces = mngmnt_interfaces
        self._ufm_ha_status_string = ""

    @staticmethod
    def _run_command(command: str):
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
        ib_to_ml_map = self._get_ib_to_ml_map()
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
                    f"{ib_interfaces_status[ib_interface]}"
                )
                result = False
        if result:
            print("All given IB interfaces are active")
        return result

    @staticmethod
    def _get_ib_to_ml_map():
        ret_code, stdout = StandbyNodeHealthChecker._run_command("ibdev2netdev")
        if ret_code != 0:
            print("Failed to run ibdev2netdev")
            return {}
        line_regex = re.compile(r"^([\w\d_]+) port \d ==> ([\w\d]+)")
        lines = stdout.splitlines()
        ib_to_mp = {}
        for line in lines:
            cur_line_match = line_regex.match(line)
            if cur_line_match:
                mlx_port = cur_line_match.group(1)
                ib_port = cur_line_match.group(2)
                ib_to_mp[ib_port] = mlx_port
        return ib_to_mp

    @staticmethod
    def _check_ib_interface(ib_interface: str, ib_interfaces_status: dict):
        if ib_interface in ib_interfaces_status:
            ib_state = ib_interfaces_status[ib_interface]["State"]
            physical_state = ib_interfaces_status[ib_interface]["Physical_state"]
            if ib_state == "active" and physical_state == "linkup":
                return True
        return False

    @staticmethod
    def _run_and_parse_ibstat():
        retcode, stdout = StandbyNodeHealthChecker._run_command("ibstat")
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

    @staticmethod
    def _run_and_parse_ip_link_show():
        ret_code, ip_link_show_output = StandbyNodeHealthChecker._run_command(
            "ip link show"
        )
        if ret_code != 0:
            print("Failed to run ip link show")
            return {}
        interfaces = StandbyNodeHealthChecker._parse_ip_link_output(ip_link_show_output)
        return interfaces

    @staticmethod
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
                    if link_type == "ether":
                        interfaces[current_interface] = state.lower()

        return interfaces

    def _check_eth_interfaces(self):
        interfaces_status = StandbyNodeHealthChecker._run_and_parse_ip_link_show()
        result = True
        for interface in self._mngmnt_interfaces:
            if interface not in interfaces_status:
                print(f"{interface} is not in the list of ether interfaces")
                result = False
            elif interfaces_status[interface] != "up":
                print(
                    f"Interface {interface} is not active {interfaces_status[interface]}"
                )
                result = False
        if result:
            print("All given ether interfaces are active")
        return result

    @staticmethod
    def _check_if_ha_is_enabled():
        command = UFM_HA_CLUSTER_COMMAND.format("is-ha")
        ret_code, stdout = StandbyNodeHealthChecker._run_command(command)
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

    @staticmethod
    def check_if_standby_node():
        command = UFM_HA_CLUSTER_COMMAND.format("is-master")
        _, stdout = StandbyNodeHealthChecker._run_command(command)
        # Not checking the ret code since it is 1 when running on the standby node
        if stdout != "standby":
            print(f"Not a standby node but {stdout}")
            return False
        print("On standby node")
        return True

    @staticmethod
    def _check_pcs_status():
        command = "pcs status"
        return_code, _ = StandbyNodeHealthChecker._run_command(command)
        if return_code != 0:
            print("pcs status is not ok, return code is {return_code}")
            return False
        print("PCS status is OK")
        return True

    @staticmethod
    def _check_corosync_rings_status():
        rings_statuses = StandbyNodeHealthChecker._run_and_parse_corosync_rings()
        if not rings_statuses:
            print("Could not find any rings")
            return False
        result = True
        for ring in rings_statuses.items():
            if not rings_statuses[ring]["status_check"]:
                text = rings_statuses[ring]["status_text"]
                print(f"Ring {ring} is {text}")
                result = False
        print("All rings are OK")
        return result

    @staticmethod
    def _run_and_parse_corosync_rings():
        # Supprting links and rings status
        ret_code, corosync_output = StandbyNodeHealthChecker._run_command(
            "corosync-cfgtool -s"
        )
        if ret_code != 0:
            print("Failed to run corosync-cfgtool -s")
            return {}

        rings_info = {}
        lines = corosync_output.splitlines()
        current_ring = None
        current_ip = None
        current_status = None

        ring_id_regex = re.compile(r"^(?:RING|LINK) ID (\d+)")
        id_ip_regex = re.compile(r"(?:id|addr)= ([\d\.]+)")
        status_regex = re.compile(r"^status+= (.+)$")
        node_status_regex = re.compile(r"^node (\d+)\: link enabled\:\d+ link connected\:\d+")

        for line in lines:
            ring_match = ring_id_regex.match(line)
            if ring_match:
                current_ring = ring_match.group(1)

            old_status_match = status_regex.match(line)
            new_status_match = node_status_regex.match(line)
            if old_status_match:
                current_status = old_status_match.group(1)
            elif new_status_match:
            id_ip_match = id_ip_regex.match(line)
            if id_ip_match:
                current_ip = id_ip_match.group(1)

            if current_ring and current_status and current_ip:
                status_check = "active with no faults" in current_status
                rings_info[current_ring] = {
                    "ip": current_ip,
                    "status_text": current_status,
                    "status_check": status_check,
                }
                current_ring = current_status = current_ip = None

        return rings_info

    @staticmethod
    def check_if_service_is_active(service_name: str):
        """
        service_name for example : pacemaker
        """
        command = SYSTEMCTL_IS_ACTIVE_COMMAND.format(service_name)
        _, stdout = StandbyNodeHealthChecker._run_command(command)
        if stdout == "active":
            print(f"Service {service_name} is active")
            return True
        print(f"Service {service_name} is not active")
        return False

    def get_ufm_ha_cluster_status_string(self):
        command = UFM_HA_CLUSTER_COMMAND.format("status")
        ret_code, res_string = StandbyNodeHealthChecker._run_command(command)
        if ret_code != 0:
            print("Failed to get ha cluster status")
            res_string = ""
        self._ufm_ha_status_string = res_string

    def _get_status_value_from_ha_cluster_status(self, keyword: str):
        for line in self._ufm_ha_status_string.splitlines():
            line = line.strip()
            if line.startswith(keyword):
                return line.split(":", 1)[-1].strip().lower()
        return None

    def check_drbd_connectivity(self):
        if not self._ufm_ha_status_string:
            return False
        drbd_connectivity_status = self._get_status_value_from_ha_cluster_status(
            "DRBD_CONNECTIVITY"
        )
        if drbd_connectivity_status != "[connected]":
            print(
                f"DRBD CONNECTIVITY status is {drbd_connectivity_status} and not Connected"
            )
            return False
        print("DRBD CONNECTIVITY status is ok (Connected)")
        return True

    def check_drdb_resource(self):
        if not self._ufm_ha_status_string:
            return False
        drdb_resource_status = self._get_status_value_from_ha_cluster_status(
            "DRBD_RESOURCE"
        )
        if drdb_resource_status != "[ha_data]":
            print(f"DRDB RESOURCE status is {drdb_resource_status} and not ha_data")
            return False
        print("DRDB RESOURCE status is ok (ha_data)")
        return True

    def check_drbd_disk_state(self):
        if not self._ufm_ha_status_string:
            return False
        drbd_disk_state = self._get_status_value_from_ha_cluster_status("DISK_STATE")
        if drbd_disk_state != "[uptodate]":
            print(f"DRBD DISK STATE status is {drbd_disk_state} and not UpToDate")
            return False
        print("DRBD DISK STATE status is ok (UpToDate)")
        return True

    def run_advanced_checks(self):
        result = True
        checks = [
            StandbyNodeHealthChecker._check_pcs_status,
            StandbyNodeHealthChecker._check_corosync_rings_status,
            self.check_drdb_resource,
            self.check_drbd_connectivity,
            self.check_drbd_disk_state,
        ]
        for check in checks:
            if not check():
                result = False
        check_with_arg = [
            (StandbyNodeHealthChecker.check_if_service_is_active, "corosync"),
            (StandbyNodeHealthChecker.check_if_service_is_active, "pacemaker"),
            (StandbyNodeHealthChecker.check_if_service_is_active, "pcsd"),
        ]
        for check, arg in check_with_arg:
            if not check(arg):
                result = False
        return result


def main(args):
    standby_node_checker = StandbyNodeHealthChecker(
        args.fabric_interfaces, args.mngmnt_interfaces
    )
    if not standby_node_checker.run_basic_checks():
        print("Due to previous failures, stopping the test")
        sys.exit(1)

    if not standby_node_checker.check_if_standby_node():
        print("The tool should only be run on Standby node")
        sys.exit(1)

    if not standby_node_checker.run_advanced_checks():
        sys.exit(1)
    print("All checks passed")


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
