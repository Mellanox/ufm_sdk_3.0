#
# Copyright © 2001-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import configparser
import json
import os
from flask_restful import Resource
from flask import request
from datetime import datetime, timedelta
from topo_diff.topo_diff import compare_topologies
import logging
import hashlib
import threading
from resources import UFMResource, Upload, Compare, Delete
from topo_diff.ndt_infra import check_file_exist,\
    DEFAULT_IBDIAGNET_NET_DUMP_PATH, check_ibdiagnet_net_dump_file_exist,\
    run_ibdiagnet, IBDIAGNET_OUT_NET_DUMP_FILE_PATH
from topo_diff.topo_diff import parse_ibdiagnet_dump,\
                        parse_ndt_file,compare_topologies_ndt_ibdiagnet
from topo_diff.ndt_infra import MERGER_OPEN_SM_CONFIG_FILE,\
    create_topoconfig_file, update_boundary_port_state_in_topoconfig_file,\
    update_last_deployed_ndt, check_duplicated_guids,\
    BOUNDARY_PORTS_STATES, IBDIAGNET_OUT_DIRECTORY,\
    IBDIAGNET_LOG_FILE, NDT_FILE_STATE_VERIFIED, NDT_FILE_STATE_DEPLOYED,\
    NDT_FILE_STATE_UPDATED, BOUNDARY_PORT_STATE_DISABLED, BOUNDARY_PORT_STATE_NO_DISCOVER,\
    NDT_FILE_STATE_UPDATED_NO_DISCOVER,NDT_FILE_STATE_UPDATED_DISABLED,\
    LAST_DEPLOYED_NDT_FILE_INFO
from resources import ReportId
from topo_diff.topo_diff import upload_topoconfig_file, SUCCESS_CODE, ACCEPTED_CODE




# ATB - TODO: need to read it from configuration or something else ....
switch_patterns = "^Port (\d+)$,(^Blade \d+_Port \d+/\d+$)"
host_patterns = "(^(SAT|DSM)\d+ ibp.*$)"


# merge specific API
class MergerNdts(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/merger_ndts_list")
        super().__init__()
        self.response_file = self.ndts_merger_list_file

    def post(self):
        return self.report_error(405, "Method is not allowed")

class MergerLatestDeployedNDT(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/merger_deployed_ndt")
        super().__init__()
        self.response_file = LAST_DEPLOYED_NDT_FILE_INFO

    def post(self):
        return self.report_error(405, "Method is not allowed")

class MergerUploadNDT(Upload):
    def __init__(self):
        super().__init__()
        self.possible_file_types = ["current_topo", "new_topo"]
        self.ndts_list_file = self.ndts_merger_list_file
        self.reports_list_file = self.reports_merger_list_file
        self.ndts_dir = self.ndts_merger_dir
        self.subnet_merger_flow = True

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def get_ndt_path(self, file_name):
        return os.path.join(self.ndts_merger_dir, file_name)


class MergerVerifyNDT(Compare):
    '''
    Class responsible for verification. It should compare received NDT file and
    network configuration discovered by ibdiagnet and read from ibdiagnet2.net_dump file
    '''
    def __init__(self):
        super().__init__({'scheduler': None})
        self.report_number = 0
        self.timestamp = ""
        self.expected_keys = ["NDT_file_path", "NDT_status"]
        self.ndts_list_file = self.ndts_merger_list_file
        self.reports_list_file = self.reports_merger_list_file
        self.ndts_dir = self.ndts_merger_dir
        self.reports_dir = self.reports_merger_dir

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def merger_report_running(self):
        '''
        Report started. Return expected report number - in case it suceed 
        '''
        next_report_number = self.get_next_report_id_number()
        if next_report_number == 0:
            return self.report_error(500, "Failed to get next report id.")
        return {"report_id": next_report_number}

    def verify(self, ndt_file_name, conf_stage="initial"):
        '''
        conf stage could be initial and advanced. Initial is when the boundary
        ports should be disable and advanced - they should be No-Discover.
        The value should be received from REST request for verification
        '''
        th = threading.Thread(target=self.run_ibdiagnet_ndt_compare, 
                              args=(ndt_file_name, conf_stage))
        th.start()
        return self.merger_report_running()

    def run_ibdiagnet_ndt_compare(self, ndt_file_name, conf_stage="initial" ):
        '''
        Function that will be called from thread - not to block UI
        and will create a report if suceed
        :param ndt_file_name:
        '''
        scope = "Single" # TODO: well ... not need it at all
        # prepare structure from NDT file
        # NDT file should be received as part of request by name
        try:
            report_content = dict()
#           Standard ibnetdiscover output is not good enough - need to check GUIDs for duplication
#           So this flow (checking for existing net_dump file to use commented)
#             if check_ibdiagnet_net_dump_file_exist():
#                 ibdiagnet_file_path = DEFAULT_IBDIAGNET_NET_DUMP_PATH
#             else:
#                 # need to run ibdiagnet and to take file from that output
            if run_ibdiagnet():
                ibdiagnet_file_path = IBDIAGNET_OUT_NET_DUMP_FILE_PATH
            else:
                raise ValueError("Report creation failed for %s: Failed to run ibdiagnet" % ndt_file_name)
            if not check_file_exist(ibdiagnet_file_path):
                raise ValueError("%s not exist" % IBDIAGNET_OUT_NET_DUMP_FILE_PATH)
            self.timestamp = self.get_timestamp()
            # check first for duplicated GUIDs in setup
            if not check_file_exist(IBDIAGNET_LOG_FILE):
                raise ValueError("%s not exist" % (IBDIAGNET_LOG_FILE))
            status, duplicated_guids = check_duplicated_guids()
            if status and duplicated_guids:
                duplication_string = duplicated_guids.decode("utf-8")
                list_dg = duplication_string.split("\n")
                duplication_error_list = ["Duplicated GUIDs detected in fabric:",]
                duplication_error_list.extend(list_dg)
                dup_guids_error_message = duplication_error_list
                raise ValueError(dup_guids_error_message)
            # get configuration from ibdiagnet
            ibdiagnet_links, ibdiagnet_links_reverse, links_info, error_message = \
                                           parse_ibdiagnet_dump(ibdiagnet_file_path)
            if error_message:
                raise ValueError(error_message)
            ndt_links = set()
            ndt_links_reversed = set()
            error_message = parse_ndt_file(ndt_links, ndt_file_name,
                             switch_patterns.split(",") + host_patterns.split(","),
                             ndt_links_reversed, True)
            if error_message:
                raise ValueError(error_message)
            # compare NDT with ibdiagnet
            # create report
            if links_info:
                #this is the structure that contains names of the nodes and ports and GUIDs
                # on base of this struct should be created topconfig file
                create_topoconfig_file(links_info, ndt_file_name, 
                            switch_patterns.split(",") + host_patterns.split(","))
            report_content = compare_topologies_ndt_ibdiagnet(self.timestamp,
                                                              ibdiagnet_links,
                                                              ibdiagnet_links_reverse,
                                                              ndt_links,
                                                              ndt_links_reversed)
            report_content["NDT file"] = ndt_file_name
            if report_content["error"]:
                response, status_code = self.create_report(scope, report_content)
                if status_code != self.success:
                    raise ValueError(report_content["error"])
        except ValueError as e:
            if "error" not in report_content:
                report_content["error"] = e.args[0]
        if "report" in report_content and not report_content["report"]["miss_wired"]\
                and not report_content["report"]["missing_in_ibdiagnet"]\
                and not report_content["report"]["missing_in_ndt"]:
            report_content["response"] = "NDT and IBDIAGNET are fully match"
            report_content.pop("error")
            report_content.pop("report")

        response, status_code = self.create_report(scope, report_content)
        if status_code != self.success:
            logging.error("Failed to create verification report: %s" % response)
        # update status of the NDT file to verified - at least once we run verification
        try:
            self.update_ndt_file_status(ndt_file_name, NDT_FILE_STATE_VERIFIED)
        except Exception as e:
            logging.error("Failed to update NDT file %s status" % ndt_file_name)

    def post(self):
        logging.info("POST /plugin/ndt_merger/merger_verify")
        logging.info("Running instant topology comparison")
        json_data = request.get_json(force=True)
        #ndt_file = json_data(ndt_record, "file", False)
        return self.verify(os.path.join(self.ndts_dir, json_data["NDT_file_name"]))


class MergerVerifyNDTReports(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/verify_ndt_reports")
        super().__init__()
        self.reports_list_file = self.reports_merger_list_file
        self.response_file = self.reports_list_file

    def post(self):
        return self.report_error(405, "Method is not allowed")

class MergerVerifyNDTReportId(ReportId):
    def __init__(self):
        logging.info("GET /plugin/ndt/verify_ndt_reports/<report_id>")
        super().__init__()
        self.reports_list_file = self.reports_merger_list_file
        self.reports_dir = self.reports_merger_dir
        # unhandled exception in case reports file was deleted manually
        with open(self.reports_list_file, "r", encoding="utf-8") as file:
            self.data = json.load(file)

class MergerDeleteNDT(Delete):
    def __init__(self):
        super().__init__()
        self.ndts_list_file = self.ndts_merger_list_file
        self.reports_list_file = self.reports_merger_list_file
        self.ndts_dir = self.ndts_merger_dir
        self.reports_dir = self.reports_merger_dir

class MergerDeployNDTConfig(UFMResource):
    '''
    Class responsible for deployment of topoconfig file to OpenSM
    it means to copy file to the opensm config directory with correct name
    '''
    def __init__(self):
        super().__init__()
        self.subnet_merger_flow = True
        self.ndts_list_file = self.ndts_merger_list_file

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def parse_request(self, json_data):
        logging.debug("Parsing JSON request: {}".format(json_data))
        try:
            self.expected_keys = ["ndt_file_name"]
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return self.report_error(status_code, response)
            self.deploy_file_name = json_data["ndt_file_name"]
        except TypeError:
            return self.report_error(400, "Failed to get NDT file name")
        return self.report_success()

    def post(self):
        '''
        Send post to upload topoconfig file to UFM server
        '''
        error_status_code, error_response = self.success, []
        info_msg = "POST /plugin/ndt/merger_deploy_ndt_config"
        logging.info(info_msg)
        json_data = request.get_json(force=True)
        logging.debug("Parsing JSON request: {}".format(json_data))
        response, status_code = self.parse_request(json_data)
        if status_code != self.success:
            return self.report_error(status_code, response)
        if not check_file_exist(MERGER_OPEN_SM_CONFIG_FILE):
            error_status_code = 400
            error_response = "Topoconfig file %s not found" % MERGER_OPEN_SM_CONFIG_FILE
            logging.info(error_response)
            return self.report_error(error_status_code, error_response)
        # create payload for request
        payload = dict()
        payload["topo_type"] = "topo_config"
        try:
            topoconf_file = open(MERGER_OPEN_SM_CONFIG_FILE, "r")
            topoconf_data = topoconf_file.read()
        except Exception as e:
            error_status_code = 400
            error_response = "Failed to read topoconfig file %s:" % (MERGER_OPEN_SM_CONFIG_FILE, e)
            logging.info(error_response)
            return self.report_error(error_status_code, error_response)
        payload["file"] = topoconf_data
        response, status_code = upload_topoconfig_file(self.ufm_port, payload)
#        if status_code != self.success:
#            return response, status_code
        # update status of the NDT file to verified - at least once we run verification
        if status_code not in (SUCCESS_CODE, ACCEPTED_CODE):
            return self.report_error(status_code, response)
        try:
            self.update_ndt_file_status(self.deploy_file_name,
                                                        NDT_FILE_STATE_DEPLOYED)
            # update last uploaded ndt file name
            update_last_deployed_ndt(self.deploy_file_name)
        except Exception as e:
            error_status_code = 400
            error_response = "Failed to update NDT file %s status: %s" % (self.deploy_file_name, e)
            logging.error(error_response)
            return response, status_code
        return self.report_success()

class MergerUpdateNDTConfig(UFMResource):
    '''
    Update last topoconfig file with boundary port state
    '''
    def __init__(self):
        super().__init__()
        self.subnet_merger_flow = True
        self.ndts_list_file = self.ndts_merger_list_file

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def parse_request(self, json_data):
        logging.debug("Parsing JSON request: {}".format(json_data))
        try:
            self.expected_keys = ["boundary_port_state", "ndt_file_name"]
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return self.report_error(status_code, response)
            boundary_port_state = json_data["boundary_port_state"]
            if boundary_port_state not in BOUNDARY_PORTS_STATES:
                error_msg = ("Boundary port state is incorrect should be one of: {}").format(",".join(BOUNDARY_PORTS_STATES))
                logging.info(error_msg)
                return self.report_error(400, error_msg)
        except TypeError:
            return self.report_error(400, "Failed to get port state")
        return self.report_success()

    def post(self):
        '''
        Post rest 
        '''
        if request.json:
            json_data = request.get_json(force=True)
            response, status_code = self.parse_request(json_data)
            if status_code != self.success:
                return response, status_code
            boundary_port_state = json_data["boundary_port_state"]
            ndt_file_name = json_data["ndt_file_name"]
            if not update_boundary_port_state_in_topoconfig_file(boundary_port_state):
                return self.report_error(400, "Failed to update topoconfig file")
            try:
                if boundary_port_state == BOUNDARY_PORT_STATE_DISABLED:
                    file_status = NDT_FILE_STATE_UPDATED_DISABLED
                elif boundary_port_state == BOUNDARY_PORT_STATE_NO_DISCOVER:
                    file_status = NDT_FILE_STATE_UPDATED_NO_DISCOVER
                else:
                    file_status = NDT_FILE_STATE_UPDATED
                self.update_ndt_file_status(ndt_file_name, file_status)
            except Exception as e:
                logging.error("Failed to update NDT file %s status: %s" % (ndt_file_name, e))
                return self.report_error(400, "Failed to update ndt file status")
            return self.report_success()
        else:
            return self.report_error(400, "Action parameters not received")


class MergerDeployConfig(UFMResource):
    def __init__(self):
        super().__init__()

class MergerMergeReportId(UFMResource):
    def __init__(self):
        super().__init__()
