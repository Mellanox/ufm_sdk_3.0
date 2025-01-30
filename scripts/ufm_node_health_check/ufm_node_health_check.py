#
# Copyright © 2013-2025 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
import signal
import subprocess
import argparse
import logging
from logging.handlers import SysLogHandler
import sys
from typing import List


def configure_logger():
    logger_name = "standby_node_health_checker"
    logger = logging.getLogger(logger_name)

    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        syslog_handler = None
        try:
            # First attempt /dev/log (default for most Unix-like systems)
            syslog_handler = SysLogHandler(address="/dev/log")
        except Exception:
            try:
                # Fallback for Red Hat or others that use /var/run/syslog
                syslog_handler = SysLogHandler(address="/var/run/syslog")
            except Exception:
                logger.warning("Syslog is not available on this system.")

        if syslog_handler:
            syslog_formatter = logging.Formatter(
                fmt="ufm_node_health_checker : [%(process)d]: %(levelname)s: %(message)s"
            )

        syslog_handler.setFormatter(syslog_formatter)
        syslog_handler.setLevel(logging.WARNING)
        logger.addHandler(syslog_handler)
    return logger


logger = configure_logger()


def set_log_level(log_level):
    """
    Change the log level to the stdout logger.
    This function does not changes the log level for the
    syslog logger.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(numeric_level)
            break


def parse_arguments():
    parser = argparse.ArgumentParser(description="Checking if standby node is ready.")

    parser.add_argument(
        "--fabric-interfaces",
        nargs="+",
        required=True,
        help="Specify one or more fabric interfaces (at least one is required), eg ib0, mlx3_0",
    )

    parser.add_argument(
        "--mgmt-interface",
        required=True,
        help="Specify one management interfaces (at least one is required), eg eth0",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args()
    return args


class UFMNodeHealthChecker:
    UFM_HA_CLUSTER_COMMAND = "ufm_ha_cluster {}"
    SYSTEMCTL_IS_ACTIVE_COMMAND = "systemctl is-active {}.service"
    IS_HA_COMMAND = UFM_HA_CLUSTER_COMMAND.format("is-ha")
    IS_MASTER_COMMAND = UFM_HA_CLUSTER_COMMAND.format("is-master")
    HA_STATUS_COMMAND = UFM_HA_CLUSTER_COMMAND.format("status")
    IBDEV2NETDEV_COMMAND = "ibdev2netdev"
    IBSTAT_COMMAND = "ibstat"
    IP_LINK_SHOW_COMMAND = "ip --json link show"
    PCS_STATUS_COMMAND = "pcs status"
    COROSYNC_RINGS_COMMAND = "corosync-cfgtool -s"
    MASTER_STRING = "master"
    STANDBY_STRING = "standby"
    DRDB_STATUS_STRING = "uptodate"
    PRIMARY_STRING = "primary"
    SECONDARY_STRING = "secondary"

    # This regex is used to translte the output of ibdev2netdev, in case
    # The user inputs ibx, we use it to find the matching mlx interface
    IBDEV2NETDEV_REGEX = re.compile(r"^([\w\d_]+) port \d ==> ([\w\d]+)")
    CORSYNC_OPTION1_RING_ID_REGEX = re.compile(r"^RING ID (\d+)")
    CORSYNC_OPTION1_RING_IP_REGEX = re.compile(r"id\ *= ([\d\.]+)")
    CORSYNC_OPTION1_STATUS_REGEX = re.compile(r"^status(?:=|:)\s*(.*)$")

    CORSYNC_OPTION2_RING_ID_REGEX = re.compile(r"^LINK ID (\d+)")
    CORSYNC_OPTION2_RING_ID_IP_REGEX = re.compile(r"addr\ *= ([\d\.]+)")
    CORSYNC_OPTION2_STATUS_REGEX = re.compile(
        r"^node (\d+):link enabled:(\d)link connected:(\d)"
    )

    CORSYNC_OPTION3_STATUS_REGEX = re.compile(r"nodeid:\s*\d+:\s*(?!localhost)(\w+)")

    def __init__(self, fabric_interfaces, mgmt_interface):
        self._fabric_interfaces = fabric_interfaces
        self._mgmt_interface = mgmt_interface
        self._ufm_ha_status_string = ""
        self._summary_actions = []
        self.node_type = None

    @classmethod
    def _run_command(cls, command: str):
        """
        The command is a string and we need to split it into an array"""
        try:
            command = command.split(" ")
            result = subprocess.run(
                command,
                shell=False,
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
        ib_to_mlx_map = self._get_ib_to_mlx_port_mapping()
        for ib_interface in self._fabric_interfaces:
            ib_interface_to_validate = ib_interface
            if not ib_interface.startswith("mlx"):
                ib_interface_to_validate = ib_to_mlx_map.get(ib_interface, ib_interface)
            if ib_interface_to_validate not in ib_interfaces_status:
                logger.warning("%s is not in the list of IB interfaces", ib_interface)
                result = False
            elif not self._check_ib_interface(
                ib_interface_to_validate, ib_interfaces_status
            ):
                logger.warning(
                    "IB interface %s is not active",
                    ib_interface,
                )
                result = False
            else:
                logger.info("%s is active", ib_interface)
        if result:
            logger.info("All given IB interfaces are active")
        return result

    @classmethod
    def _get_ib_to_mlx_port_mapping(cls):
        ret_code, stdout = cls._run_command(cls.IBDEV2NETDEV_COMMAND)
        if ret_code != 0:
            logger.error("Failed to run ibdev2netdev")
            return {}
        lines = stdout.splitlines()
        ib_to_mlx_map = {}
        for line in lines:
            cur_line_match = cls.IBDEV2NETDEV_REGEX.match(line)
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
        retcode, stdout = cls._run_command(cls.IBSTAT_COMMAND)
        if retcode != 0:
            logger.error("Cannot run ibstat")
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
        ret_code, ip_link_show_output = cls._run_command(cls.IP_LINK_SHOW_COMMAND)
        if ret_code != 0:
            logger.error("Failed to run ip link show")
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
            logger.error("Error while parssing ib link show command")
        return interfaces

    def _check_mgmt_interface(self):
        interfaces_status = self._run_and_parse_ip_link_show()
        result = True
        if self._mgmt_interface not in interfaces_status:
            logger.warning(
                "%s is not in the list of management interfaces", self._mgmt_interface
            )
            result = False
        elif interfaces_status[self._mgmt_interface] != "up":
            logger.warning(
                "Interface %s is not active %s",
                self._mgmt_interface,
                interfaces_status[self._mgmt_interface],
            )
            result = False
        else:
            logger.info("%s is active", self._mgmt_interface)
        if result:
            logger.info("The given management interface is active")
        return result

    def _check_if_ha_is_enabled(self):
        logger.info("Checking if ha is enabled")
        ret_code, stdout = self._run_command(self.IS_HA_COMMAND)
        if ret_code != 0 or stdout.lower() != "yes":
            logger.error("HA is not enabled")
            self._summary_actions.append("HA cluster is not enabled")
            return False
        logger.info("HA is enabled")
        return True

    def run_all_checks(self):
        self._check_if_ha_is_enabled()
        self._check_and_set_node_type()
        self._check_interfaces()
        self._check_pcs_status()
        self._check_services()
        self._check_drbd()

    def _check_drbd(self):
        logger.info("Checking DRBD")
        self.set_ufm_ha_cluster_status_string()
        drdb_passed = (
            self.check_drdb_role()
            and self.check_drbd_connectivity()
            and self.check_drbd_disk_state()
        )
        if not drdb_passed:
            self._summary_actions.append("DRDB is not healthy")

    def _check_services(self):
        logger.info("Checking HA services status")
        tests_passed = (
            self.check_if_service_is_active("corosync")
            and self._check_corosync_rings_status()
            and self.check_if_service_is_active("pacemaker")
            and self.check_if_service_is_active("pcsd")
        )
        if not tests_passed:
            self._summary_actions.append("Some critical services are down")

    def _check_interfaces(self):
        logger.info("Checking interfaces status")
        interfaces_passed = self._check_ib_interfaces() and self._check_mgmt_interface()
        if not interfaces_passed:
            logger.error("Some interfaces checks failed")
            self._summary_actions.append("IB/Mgmt interfaces are down")

    def _check_and_set_node_type(self):
        _, stdout = self._run_command(self.IS_MASTER_COMMAND)
        # Not checking the ret code since it is 1 when running on the standby node
        if stdout != self.STANDBY_STRING and stdout != self.MASTER_STRING:
            error_msg = (
                f"The script is not running on master or standby-node, but on {stdout}."
                "Please make sure to run it on one of the UFM HA cluster nodes."
            )
            logger.error(error_msg)
            self._summary_actions.append(error_msg)
            return False
        self.node_type = stdout
        logger.info("Success - The script is running on a %s node", stdout)
        return True

    def _check_pcs_status(self):
        logger.info("Checking PCS status")
        return_code, _ = self._run_command(self.PCS_STATUS_COMMAND)
        if return_code != 0:
            logger.error("pcs status is not ok, return code is %s", return_code)
            self._summary_actions.append("PCS is down")
            return False
        logger.info("PCS status is OK")
        return True

    @classmethod
    def _check_corosync_rings_status(cls):
        logger.info("Checking HA interfaces")
        ret_code, corosync_output = cls._run_command(cls.COROSYNC_RINGS_COMMAND)
        if ret_code != 0:
            logger.error("Failed to run corosync-cfgtool -s")
            return {}
        corosync_output_lines = corosync_output.splitlines()
        checks_to_run = [
            cls._parse_corsync_rings_output_option1,
            cls._parse_corsync_rings_output_option2,
            cls._parse_corsync_rings_output_option3,
        ]
        for check_option in checks_to_run:
            rings_statuses = check_option(corosync_output_lines)
            if rings_statuses:
                break
        if not rings_statuses:
            logger.error("Could not find any corosync rings status")
            return False
        result = True
        try:
            for ring in rings_statuses:
                if not rings_statuses[ring]["status_check"]:
                    text = rings_statuses[ring]["status_text"]
                    if text:
                        logger.error("%s is not OK - %s", ring, text)
                    else:
                        logger.error("%s has an empty status", ring)
                    result = False
        except Exception:
            logger.exception("Failed to parse corosync rings status")
            return False
        if result:
            logger.info("All corosync rings are OK")
        return result

    @classmethod
    def _parse_corsync_rings_output_option1(cls, corosync_output_lines: List[str]):
        # This function handles the another output of corsync, for example:
        # Printing ring status.
        # Local node ID 2
        # RING ID 0
        # 	id	= 11.0.0.11
        # 	status	= ring 0 active with no faults
        # RING ID 1
        # 	id	= 10.209.44.110
        # 	status	= ring 1 active with no faults
        rings_info = {}
        current_ring = None
        current_ip = None
        for line in corosync_output_lines:
            ring_match = cls.CORSYNC_OPTION1_RING_ID_REGEX.match(line)
            if ring_match:
                current_ring = ring_match.group(1)
            ring_ip = cls.CORSYNC_OPTION1_RING_IP_REGEX.match(line)
            if ring_ip:
                current_ip = ring_ip.group(1)
            status_match = cls.CORSYNC_OPTION1_STATUS_REGEX.match(line)
            if current_ring and current_ip and status_match is not None:
                status_text = status_match.group(1)
                status_check = "active with no faults" in status_text
                rings_info[f"Ring {current_ring}"] = {
                    "ip": current_ip,
                    "status_text": status_text,
                    "status_check": status_check,
                }
                current_ring = current_ip = None
        return rings_info

    @classmethod
    def _parse_corsync_rings_output_option2(cls, corosync_output_lines: List[str]):
        # This function handles another output of corsync, for example:
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
        current_ring = None
        current_ip = None
        for line in corosync_output_lines:
            ring_match = cls.CORSYNC_OPTION2_RING_ID_REGEX.match(line)
            if ring_match:
                current_ring = ring_match.group(1)
            ring_ip = cls.CORSYNC_OPTION2_RING_ID_IP_REGEX.match(line)
            if ring_ip:
                current_ip = ring_ip.group(1)
            status_match = cls.CORSYNC_OPTION2_STATUS_REGEX.match(line)
            if current_ring and current_ip and status_match:
                node_id = status_match.group(1)
                link_enabled = status_match.group(2)
                link_connected = status_match.group(3)
                status_check = link_enabled == "1" and link_connected == "1"
                rings_info[f"Link {current_ring} Node {node_id}"] = {
                    "ip": current_ip,
                    "status_text": f"node {node_id}"
                    f"link enabled:{link_enabled} "
                    f"link connected:{link_connected}",
                    "status_check": status_check,
                }
        return rings_info

    @classmethod
    def _parse_corsync_rings_output_option3(cls, corosync_output_lines: List[str]):
        # This function handles another output of corsync, for example:
        # Local node ID 2, transport knet
        # LINK ID 0 udp
        # 	addr	= 10.209.226.116
        # 	status:
        # 		nodeid:          1:	connected
        # 		nodeid:          2:	localhost
        # LINK ID 1 udp
        # 	addr	= 1.1.36.14
        # 	status:
        # 		nodeid:          1:	connected
        # 		nodeid:          2:	localhost
        rings_info = {}
        current_ring = None
        current_ip = None
        for line in corosync_output_lines:
            ring_match = cls.CORSYNC_OPTION2_RING_ID_REGEX.match(line)
            if ring_match:
                current_ring = ring_match.group(1)
            ring_ip = cls.CORSYNC_OPTION2_RING_ID_IP_REGEX.match(line)
            if ring_ip:
                current_ip = ring_ip.group(1)
            status_match = cls.CORSYNC_OPTION3_STATUS_REGEX.match(line)
            if current_ring and current_ip and status_match:
                link_connected = status_match.group(1)
                status_check = link_connected == "connected"
                rings_info[f"Link {current_ring}"] = {
                    "ip": current_ip,
                    "status_text": f"link {current_ring}"
                    f"link connected:{link_connected}",
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
            logger.info("Service %s is active", service_name)
            return True
        logger.error("Service %s is not active", service_name)
        return False

    def set_ufm_ha_cluster_status_string(self):
        ret_code, res_string = self._run_command(self.HA_STATUS_COMMAND)
        if ret_code != 0:
            logger.error("Failed to get ha cluster status")
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
            logger.error(
                "DRBD CONNECTIVITY status is %s and not Connected",
                drbd_connectivity_status,
            )
            return False
        logger.info("DRBD CONNECTIVITY status is ok - Connected")
        return True

    def check_drdb_role(self):
        if not self._ufm_ha_status_string:
            return False
        drdb_resource_status = self._get_status_value_from_ha_cluster_status(
            "DRBD_ROLE"
        )
        if not self.node_type:
            logger.warning("Skipping drdb ROLE check since we or an unkown node type")
            return False
        if (
            self.node_type == self.MASTER_STRING
            and drdb_resource_status != self.PRIMARY_STRING
        ):
            logger.error("DRBD ROLE status is %s and not Primary", drdb_resource_status)
            return False
        if (
            self.node_type == self.STANDBY_STRING
            and drdb_resource_status != self.SECONDARY_STRING
        ):
            logger.error(
                "DRDB ROLE status is %s and not Secondary", drdb_resource_status
            )
            return False
        logger.info("DRDB ROLE status is ok - %s", drdb_resource_status)
        return True

    def print_summary_information(self):
        logger.info("")
        logger.info("Executive summary:")
        # If there is anything in the summary actions it means we have failures
        if len(self._summary_actions) > 0:
            for row in self._summary_actions:
                logger.info(row)
            return False
        logger.info("This UFM node is configured correctly")
        return True

    def check_drbd_disk_state(self):
        if not self._ufm_ha_status_string:
            return False
        drbd_disk_state = self._get_status_value_from_ha_cluster_status("DISK_STATE")
        if drbd_disk_state != self.DRDB_STATUS_STRING:
            logger.error(
                "DRBD DISK STATE status is %d and not UpToDate", drbd_disk_state
            )
            return False
        logger.info("DRBD DISK STATE status is ok - UpToDate")
        return True


def main(args):
    ufm_node_checker = UFMNodeHealthChecker(args.fabric_interfaces, args.mgmt_interface)
    logger.info("Starting the ufm node health checks")

    ufm_node_checker.run_all_checks()
    logger.info("Done running the ufm node health checks")

    any_failures = ufm_node_checker.print_summary_information()
    sys.exit(not any_failures)


def handle_sigterm(_, __):
    print("SIGTERM received. Exiting...")
    sys.exit(1)


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGTERM, handle_sigterm)
        args = parse_arguments()
        set_log_level(args.log_level)
        main(args)
    except Exception:
        logger.fatal("Fatal while running the tests", exc_info=True)
