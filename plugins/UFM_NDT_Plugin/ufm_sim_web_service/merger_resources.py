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
import http
import io
import threading
from resources import UFMResource, Upload, Compare, Delete
from topo_diff.ndt_infra import check_file_exist,\
    DEFAULT_IBDIAGNET_NET_DUMP_PATH, IBDIAGNET_OUT_DB_CSV_FILE_PATH,check_ibdiagnet_net_dump_file_exist,\
    run_ibdiagnet, check_boundary_port_state, IBDIAGNET_OUT_NET_DUMP_FILE_PATH
from topo_diff.topo_diff import parse_ibdiagnet_dump, \
                        parse_ndt_file,compare_topologies_ndt_ibdiagnet
from topo_diff.ndt_infra import MERGER_OPEN_SM_CONFIG_FILE,\
    create_topoconfig_file, update_boundary_port_state_in_topoconfig_file,\
    update_last_deployed_ndt, check_duplicated_guids, create_raw_topoconfig_file, \
    update_cv_credentials, read_cv_credentials, update_cv_host_in_config_file, \
    check_duplicated_node_descriptions, \
    BOUNDARY_PORTS_STATES, IBDIAGNET_OUT_DIRECTORY, \
    IBDIAGNET_LOG_FILE, NDT_FILE_STATE_VERIFIED, NDT_FILE_STATE_DEPLOYED,\
    NDT_FILE_STATE_UPDATED, BOUNDARY_PORT_STATE_DISABLED, BOUNDARY_PORT_STATE_NO_DISCOVER,\
    NDT_FILE_STATE_UPDATED_NO_DISCOVER,NDT_FILE_STATE_UPDATED_DISABLED,LOCAL_HOST_VALUES, \
    LAST_DEPLOYED_NDT_FILE_INFO, NDT_FILE_STATE_VERIFY_FILED, \
    NDT_FILE_STATUS_VERIFICATION_FAILED, CABLE_VALIDATION_REQUEST_PORT
from resources import ReportId
from topo_diff.topo_diff import upload_topoconfig_file, get_cable_validation_report, \
                                get_local_cable_validation_report, \
                                SUCCESS_CODE, ACCEPTED_CODE
from topo_diff.ndt_infra import get_topoconfig_file_name
import pandas as pd

# merge specific API
class MergerNdts(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/merger_ndts_list")
        super().__init__()
        self.response_file = self.ndts_merger_list_file

    def post(self):
        return self.report_error(405, "Method is not allowed")

class MergerNdtsFile(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/merger_ndts_list/<ndt_file_name>")
        super().__init__()
        self.ndts_list_file = self.ndts_merger_list_file
        self.reports_list_file = self.reports_merger_list_file
        self.ndts_dir = self.ndts_merger_dir
        self.subnet_merger_flow = True

    def get(self, ndt_file_name):
        logging.info("GET /plugin/ndt/merger_ndts_list/<ndt_file_name>")
        # unhandled exception in case reports file was changed manually
        file_name = ndt_file_name
        file_path = os.path.join(self.ndts_dir, file_name)
        ndt_file_properties = None
        if not check_file_exist(file_path):
            return self.report_error(400, "NDT file '{}' does not exist".format(file_name))
        try:
            with open(self.ndts_list_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            for entry in data:
                if entry["file"] == ndt_file_name:
                    ndt_file_properties = entry
                    break
        except Exception as e:
            error_message = "Failed to read data from NDTs list file: %s" % e
            logging.error(error_message)
            return self.report_error(400, {error_message})
        if not ndt_file_properties:
            error_message = "NDT file {} not found".format(ndt_file_name)
            logging.error(error_message)
            return self.report_error(400, {error_message})
        return self.report_success(ndt_file_properties)

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
        self.ndts_list_file = self.ndts_merger_list_file
        self.reports_list_file = self.reports_merger_list_file
        self.ndts_dir = self.ndts_merger_dir
        self.subnet_merger_flow = True

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def get_ndt_path(self, file_name):
        return os.path.join(self.ndts_merger_dir, file_name)

    def post(self):
        '''
        Upload NDT file
        '''
        info_msg = "POST /plugin/ndt/merger_upload_ndt"
        logging.info(info_msg)
        image_file = request.files.get('file', None)
        if image_file is None:
            error_response = 'The file property is missing from the request'
            return self.report_error(http.client.BAD_REQUEST, error_response)
        self.file_name = image_file.filename
        file_content = (image_file.read()).decode('ascii')
        file_content = file_content.replace('\r\n', '\n')
        response, status_code = self.update_ndts_list()
        if status_code != self.success:
            return self.report_error(status_code, response)
        response, status_code = self.save_ndt(file_content)
        if status_code != self.success:
            return self.report_error(status_code, response)
        ret_params = {"ndt_file_name": self.file_name}
        return self.report_success(ret_params)

class MergerVerifyNDT(Compare):
    '''
    Class responsible for verification. It should compare received NDT file and
    network configuration discovered by ibdiagnet and read from ibdiagnet2.net_dump file
    '''
    def __init__(self):
        super().__init__({'scheduler': None})
        self.report_number = 0
        self.timestamp = ""
        self.expected_keys = ["ndt_file_name", "NDT_status"]
        self.ndts_list_file = self.ndts_merger_list_file
        self.reports_list_file = self.reports_merger_list_file
        self.ndts_dir = self.ndts_merger_dir
        self.reports_dir = self.reports_merger_dir

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def merger_report_running(self, ndt_file_name):
        '''
        Report started. Return expected report number - in case it succeed
        '''
        return {"ndt_file_name": os.path.basename(ndt_file_name),
                "report_id": self.report_number}

    def create_merger_report_running(self, ndt_file_name):
        '''
        Create a report with report running status - running
        Will be overwritten by "real" report when completed
        :param ndt_file_name: name of the report file - string
        '''
        self.timestamp = self.get_timestamp()
        report_content = {
        "status": "running",
        "error": "",
        "timestamp": self.timestamp,
        "NDT_file": ndt_file_name,
        "report": ""
        }
        return self.create_report_started(report_content)

    def create_report_started(self, report_content):
        '''
        Create report with mention it is started to run
        :param report_content:
        '''
        scope = "Single"
        return self.create_report(scope, report_content, False)

    def verify(self, ndt_file_name):
        '''
        conf stage could be initial and advanced. Initial is when the boundary
        ports should be disable and advanced - they should be No-Discover.
        The value should be received from REST request for verification
        '''
        # create an empty report with status running
        
        response, status_code = self.create_merger_report_running(ndt_file_name)
        if status_code != self.success:
            logging.error("Failed to create initial report for: %s verification" % ndt_file_name)
            return self.report_error(status_code, response)
        ndt_compare_thread = threading.Thread(target=self.run_ibdiagnet_ndt_compare,
                              args=(ndt_file_name,))
        ndt_compare_thread.start()
        return self.merger_report_running(ndt_file_name)

    def run_ibdiagnet_ndt_compare(self, ndt_file_name):
        '''
        Function that will be called from thread - not to block UI
        and will create a report if succeed
        :param ndt_file_name:
        '''
        scope = "Single" # TODO: well ... not need it at all
        # prepare structure from NDT file
        # NDT file should be received as part of request by name
        ndt_status = NDT_FILE_STATE_VERIFIED
        try:
            report_content = dict()
            # place holder for duplicated node description to be included in final report
            duplicated_nd_list = []
            # basic report in case of failure
            report_content["timestamp"] = self.timestamp
            report_content["report"] = {}
            report_content["NDT_file"] = os.path.basename(ndt_file_name)
            # Check if we're in test mode and have a predefined ibdiagnet output path
            if self.merger_test_mode and self.predefined_ibdiagnet_output_path:
                ibdiagnet_file_path = os.path.join(self.predefined_ibdiagnet_output_path, 'ibdiagnet2.db_csv')
                if not os.path.exists(ibdiagnet_file_path):
                    report_content["error"] = f"Predefined db_csv file not found at {ibdiagnet_file_path}"
                    report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                    raise ValueError(report_content["error"])
            else:
                if run_ibdiagnet():
                    ibdiagnet_file_path = IBDIAGNET_OUT_DB_CSV_FILE_PATH
                else:
                    report_content["error"] = "Report creation failed for %s: Failed to run ibdiagnet" % ndt_file_name
                    report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                    raise ValueError(report_content["error"])
            if self.merger_test_mode and self.predefined_ibdiagnet_output_path:
                # if test mode is enabled and predefined ibdiagnet output path is set, set correct path to ibdiagnet2.log file
                ibdiagnet_log_file = os.path.join(self.predefined_ibdiagnet_output_path, 'ibdiagnet2.log')
            else:
                ibdiagnet_log_file = IBDIAGNET_LOG_FILE
            if not check_file_exist(ibdiagnet_file_path):
                report_content["error"] = "Report creation failed for %s: File %s not exists" % (ndt_file_name, IBDIAGNET_OUT_NET_DUMP_FILE_PATH)
                report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                raise ValueError(report_content["error"])
            self.timestamp = self.get_timestamp()
            # check first for duplicated GUIDs in setup
            if not check_file_exist(ibdiagnet_log_file):
                report_content["error"] = "Report creation failed for %s: Filed to check duplicated GUIDs. File %s not exists" % (ndt_file_name, IBDIAGNET_LOG_FILE)
                report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                raise ValueError(report_content["error"])
            status, duplicated_guids = check_duplicated_guids()
            if status and duplicated_guids:
                # in case of duplicated GUIDs verification of links will not be performed
                duplication_string = duplicated_guids.decode("utf-8")
                list_dg = duplication_string.split("\n")
                report_content = self.create_duplicated_guids_content(list_dg, ndt_file_name)
                response, status_code = self.create_report(scope, report_content, True)
                if status_code != self.success:
                    raise ValueError(report_content["error"])
                else:
                    report_content["error"] = "Report creation failed for %s: Filed to check duplicated GUIDs. File %s not exists" % (ndt_file_name, IBDIAGNET_LOG_FILE)
                    report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                    raise ValueError(report_content["error"])
            if self.include_duplicated_nd:
                # check for duplicated node descriptions
                status, duplicated_nd = check_duplicated_node_descriptions()
                if status and duplicated_nd:
                    # in case of duplicated ND - include records in final report
                    # (notification only - no report failure)
                    duplication_nd_string = duplicated_nd.decode("utf-8")
                    duplicated_nd_list = duplication_nd_string.split("\n")
            # get configuration from ibdiagnet
            ibdiagnet_links, ibdiagnet_links_reverse, links_info, node_description_to_guid_dict, node_description_port_lablel_to_port_number_dict,error_message = \
                                           parse_ibdiagnet_dump(ibdiagnet_file_path)
            if error_message:
                report_content["error"] = error_message
                report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                raise ValueError(error_message)
            ndt_links = set()
            ndt_links_reversed = set()
            error_message = parse_ndt_file(ndt_links, ndt_file_name,
                            self.switch_patterns + self.host_patterns,
                            ndt_links_reversed, True)
            if error_message:
                report_content["error"] = error_message
                report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                raise ValueError(error_message)
            # compare NDT with ibdiagnet
            # create report
            if not links_info:
                report_content["error"] = "Failed to create topoconfig file. No links found"
                report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                raise ValueError(report_content["error"])
            report_content = compare_topologies_ndt_ibdiagnet(self.timestamp,
                                                              ibdiagnet_links,
                                                              ibdiagnet_links_reverse,
                                                              ndt_links,
                                                              ndt_links_reversed)
            # Add to report entries with duplicated node description
            if duplicated_nd_list:
                if "report" not in report_content or not isinstance(report_content["report"], list):
                    report_content["report"] = []
                report_content["status"] = "Completed with errors"
            for duplicated_nd_entry in duplicated_nd_list:
                if duplicated_nd_entry:
                    report_item = {"category": "duplicated node description",
                               "description": duplicated_nd_entry.split(",")[-1].strip("\"")}
                    report_content["report"].append(report_item)
            report_content["NDT_file"] = os.path.basename(ndt_file_name)
            topoconfig_creation_status, message, failed_ports = create_topoconfig_file(links_info,
                      ndt_file_name, self.switch_patterns + self.host_patterns,
                      node_description_to_guid_dict, node_description_port_lablel_to_port_number_dict)
            if not topoconfig_creation_status or failed_ports:
                report_content["error"] = message
                report_content["status"] = NDT_FILE_STATUS_VERIFICATION_FAILED
                logging.error(message)
                raise ValueError(report_content["error"])
            if report_content["error"]:
                response, status_code = self.create_report(scope, report_content)
                if status_code != self.success:
                    raise ValueError(report_content["error"])
        except ValueError as e:
            if "error" not in report_content:
                report_content["error"] = e.args[0]
        except Exception as e:
            if "error" not in report_content:
                report_content["error"] = "Unhandeled error %s" % e
        response, status_code = self.create_report(scope, report_content)
        if status_code != self.success:
            logging.error("Failed to create verification report: %s" % response)
        # update status of the NDT file to verified - at least once we run verification
        try:
            self.update_ndt_file_status(ndt_file_name, ndt_status)
        except Exception as e:
            logging.error("Failed to update NDT file %s status" % ndt_file_name)

    def create_duplicated_guids_content(self, list_dg, ndt_file_name):
        '''
        Create report context of duplicated guids
        :param list_dg: list of duplicated guids
        '''
        dg_category = "duplicated guids"
        report_content = {
        "status": "Completed with critical errors",
        "error": "",
        "timestamp": self.timestamp,
        "NDT_file": os.path.basename(ndt_file_name),
        "report": []
        }
        for duplicated_guid in list_dg:
            dg_entry = {
                "category": dg_category,
                "description": duplicated_guid
                }
            report_content["report"].append(dg_entry)
        return report_content

    def post(self):
        logging.info("POST /plugin/ndt_merger/merger_verify")
        logging.info("Running instant topology comparison")
        json_data = request.get_json(force=True)
        #ndt_file = json_data(ndt_record, "file", False)
        return self.verify(os.path.join(self.ndts_dir, json_data["ndt_file_name"]))

    def get_next_report_id_number(self):
        '''
        Return next expected report number
        '''
        next_report_number = 0 # initial value - will cause an error return
        with open(self.reports_list_file, "r", encoding="utf-8") as reports_list_file:
            # unhandled exception in case reports file was changed manually
            data = json.load(reports_list_file)
            next_report_number = len(data) + 1
        return next_report_number

    def update_reports_list(self, scope, ndt_file_name, completed):
        if completed:
            # no need to update report list
            return self.report_success()
        with open(self.reports_list_file, "r", encoding="utf-8") as reports_list_file:
            # unhandled exception in case reports file was changed manually
            data = json.load(reports_list_file)
            self.report_number = len(data) + 1
            entry = {"report_id": self.report_number,
                     "report_scope": scope,
                     "NDT_file": ndt_file_name,
                     "timestamp": self.timestamp}
            data.append(entry)
        with open(self.reports_list_file, "w") as reports_list_file:
            json.dump(data, reports_list_file)
        return self.report_success()


class MergerVerifyNDTReports(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/merger_verify_ndt_reports")
        super().__init__()
        self.reports_list_file = self.reports_merger_list_file
        self.response_file = self.reports_list_file

    def post(self):
        return self.report_error(405, "Method is not allowed")

class MergerVerifyNDTReportId(ReportId):
    def __init__(self):
        logging.info("GET /plugin/ndt/merger_verify_ndt_reports/<report_id>")
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

    def delete_ndt_reports(self, ndt:str):
        '''
        Delete reports related to NDT file
        :param ndt: name of NDT file
        '''
        # find reports related to NDT file name and remove them.
        # Update reports.json file
        try:
            with open(self.reports_list_file, "r", encoding="utf-8") as reports_list_file:
                # unhandled exception in case reports file was changed manually
                data = json.load(reports_list_file)
                data_to_proceed = data.copy()
                for report_data in data_to_proceed:
                    if os.path.basename(report_data.get("NDT_file", "")) == ndt:
                        report_name = "report_{}.json".format(report_data["report_id"])
                        report_path = self.get_report_path(report_name)
                        if check_file_exist(report_path):
                            os.remove(report_path)
                        data.remove(report_data)
            with open(self.reports_list_file, "w") as reports_list_file:
                json.dump(data, reports_list_file)
        except Exception as e:
            return self.report_error(400, "Failed to delete reports for NDT file %s: %s" % (ndt, e))
        return [], self.success


class MergerDeployNDTConfig(UFMResource):
    '''
    Class responsible for deployment of topoconfig file to OpenSM
    it means to copy file to the opensm config directory with correct name
    '''
    def __init__(self):
        super().__init__()
        self.subnet_merger_flow = True
        self.ndts_list_file = self.ndts_merger_list_file
        self.expected_keys = ["ndt_file_name"]

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def parse_request(self, json_data):
        logging.debug("Parsing JSON request: {}".format(json_data))
        try:
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return self.report_error(status_code, response)
        except TypeError:
            return self.report_error(400, "Failed to get NDT file name")
        return self.report_success()

    def post_upload_topoconfig_file(self, topoconfig_file_name):
        '''
        upload topoconfig file to UFM
        '''
                # create payload for request
        payload = dict()
        payload["topo_type"] = "topo_config"
        try:
            topoconf_file = open(topoconfig_file_name, "r")
            topoconf_data = topoconf_file.read()
        except Exception as e:
            error_status_code = 400
            error_response = "Failed to read topoconfig file %s:" % (topoconfig_file_name, e)
            logging.info(error_response)
            return self.report_error(error_status_code, error_response)
        payload["file"] = topoconf_data
        response, status_code = upload_topoconfig_file(self.ufm_port, payload)
#        if status_code != self.success:
#            return response, status_code
        # update status of the NDT file to verified - at least once we run verification
        if status_code not in (SUCCESS_CODE, ACCEPTED_CODE):
            return self.report_error(status_code, response)
        if not check_boundary_port_state(self.port_validation_sleep_interval,
                                         self.port_validation_number_of_attempts,
                                         self.deploy_file_name):
            error_status_code = 400
            error_response = "Failure: boundary ports state was not changed by OpenSM. No topology changes deployed."
            logging.error(error_response)
            return self.report_error(error_status_code, error_response)
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
        self.deploy_file_name = json_data["ndt_file_name"]
        topoconfig_file_name = get_topoconfig_file_name(self.deploy_file_name)
        if not check_file_exist(topoconfig_file_name):
            error_status_code = 400
            error_response = "Topoconfig file %s not found" % topoconfig_file_name
            logging.info(error_response)
            return self.report_error(error_status_code, error_response)
        return self.post_upload_topoconfig_file(topoconfig_file_name)

class MergerUpdDeployNDTConfig(MergerDeployNDTConfig):
    '''
    Same action to set boundary ports state to received in request and to deploy
    topoconfig to UFM server
    '''
    def __init__(self):
        super().__init__()
        self.expected_keys = ["ndt_file_name", "boundary_port_state"]

    def post(self):
        '''
        Send post to update topoconfig and to upload topoconfig file to UFM server
        '''
        error_status_code, error_response = self.success, []
        info_msg = "POST /plugin/ndtmerger_update_deploy_ndt_config"
        logging.info(info_msg)
        json_data = request.get_json(force=True)
        logging.debug("Parsing JSON request: {}".format(json_data))
        response, status_code = self.parse_request(json_data)
        self.deploy_file_name = json_data["ndt_file_name"]
        self.boundary_port_state = json_data["boundary_port_state"]
        topoconfig_file_name = get_topoconfig_file_name(self.deploy_file_name)
        if status_code != self.success:
            return self.report_error(status_code, response)
        if not check_file_exist(topoconfig_file_name):
            error_status_code = 400
            error_response = "Topoconfig file %s not found" % topoconfig_file_name
            logging.info(error_response)
            return self.report_error(error_status_code, error_response)
        # update topoconfig file with received boundary_port_state
        if not update_boundary_port_state_in_topoconfig_file(self.boundary_port_state,
                                                             self.deploy_file_name):
            return self.report_error(400, "Failed to update topoconfig file")
        try:
            if self.boundary_port_state == BOUNDARY_PORT_STATE_DISABLED:
                file_status = NDT_FILE_STATE_UPDATED_DISABLED
            elif self.boundary_port_state == BOUNDARY_PORT_STATE_NO_DISCOVER:
                file_status = NDT_FILE_STATE_UPDATED_NO_DISCOVER
            else:
                file_status = NDT_FILE_STATE_UPDATED
            self.update_ndt_file_status(self.deploy_file_name, file_status)
        except Exception as e:
            logging.error("Failed to update NDT file %s status: %s" % (self.deploy_file_name, e))
            return self.report_error(400, "Failed to update ndt file status")
        return self.post_upload_topoconfig_file(topoconfig_file_name)

class MergerCreateNDTTopoconfig(UFMResource):
    '''
    Just create topoconfig on base of NDT file - no verification
    Just include links that exist in NDT and in ibdiagnet output with boundary
    ports in mode that received as parameter
    '''
    def __init__(self):
        super().__init__()
        self.subnet_merger_flow = True
        self.ndts_list_file = self.ndts_merger_list_file
        self.ndts_dir = self.ndts_merger_dir

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
            ndt_file_path = os.path.join(self.ndts_dir, json_data["ndt_file_name"])
            status, error_message = create_raw_topoconfig_file(ndt_file_path, boundary_port_state,
                                    self.switch_patterns + self.host_patterns,
                                    test_mode=self.merger_test_mode,
                                    predefined_ibdiagnet_output_path=self.predefined_ibdiagnet_output_path)
            if not status:
                return self.report_error(400, error_message)
            return self.report_success()
        else:
            return self.report_error(400, "Create topoconfig: Action parameters not received")

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
            if not update_boundary_port_state_in_topoconfig_file(boundary_port_state,
                                                                 ndt_file_name):
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

class MergerCableValidationReport(UFMResource):
    '''
    Handle cable validation request - send request to cable validation plugin
    and send respond back
    '''
    def __init__(self):
        super().__init__()

    def get(self):
        '''
        Get cable validation report
        '''
        if not self.cable_validation_server_addr:
            error_status_code = 400
            error_response = "Failure: Cable validation server address not defined in config file."
            logging.error(error_response)
            return self.report_error(error_status_code, error_response)
        # check if local request or remote and read credentials from config if need...
        if self.cable_validation_server_addr in LOCAL_HOST_VALUES:
            # local request - no need credentials
            logging.info(f"Getting cable validation report from localhost")
            result, status_code = get_local_cable_validation_report(self.ufm_port)
        else:
            cv_username, cv_password = read_cv_credentials(self.cv_credentials_path)
            if cv_username and cv_password:
                logging.info(f"Getting cable validation report from server {self.cable_validation_server_addr}")
                result, status_code = get_cable_validation_report(self.cable_validation_server_addr,
                                           self.cable_validation_request_port,
                                           cv_username, cv_password)
            else:
                return self.report_error(status_code, "Failed to read cable validation credentials.")
        if result:
            logging.info("Dispatch requested Cable Validation Report to user.")
            return self.report_success(result)
        else:
            return self.report_error(status_code, "No cable validation report data was retrieved")

    def post(self):
        '''
        Post rest 
        '''
        return self.report_error(405, "Method is not allowed")


class MergerCableValidationEnabled(UFMResource):
    '''
    If cable validation server address set
    and send respond back
    '''
    def __init__(self):
        super().__init__()

    def get(self):
        '''
        Get rest 
        '''
        if self.cable_validation_server_addr:
            return self.report_success()
        else:
            return self.report_error(400, "Cable validation is not enabled.")

    def post(self):
        '''
        Post rest 
        '''
        return self.report_error(405, "Method is not allowed")


class MergerCableValidationConnectionCfg(UFMResource):
    '''
    Class to manage connectivity configuration to cable validation plugin.
    '''
    def __init__(self):
        super().__init__()

    def get(self):
        '''
        Send respond with connectivity parameters
        '''
        logging.info("GET /plugin/ndt/cable_validation_connection_configuration")
        # read credentials and info from credential file
        # read credentials
        # check config
        responce_dict = {}
        if not self.cable_validation_server_addr: # no cv server defined
            responce_dict["is_enabled"] = False
        elif self.cable_validation_server_addr in LOCAL_HOST_VALUES:
            responce_dict["mode"] = "local"
            responce_dict["is_enabled"] = True
            return self.report_success(responce_dict)
        else:
            responce_dict["mode"] = "remote"
            responce_dict["is_enabled"] = True
            responce_dict["address"] = self.cable_validation_server_addr
            responce_dict["port"] = self.cable_validation_request_port
            cv_username, cv_password = read_cv_credentials(self.cv_credentials_path)
            if cv_username and cv_password:
                responce_dict["username"] = cv_username
            else:
                # failed to read 
                error_message = "Failed to read credentials from file %s" % self.cv_credentials_path
                logging.error(error_message)
                return self.report_error(400, {error_message})
        return self.report_success(responce_dict)

    def parse_request(self, json_data):
        '''
        Validate received request parameters
        :param json_data:
        '''
        logging.debug("Parsing JSON request: {}".format(json_data))
        try:
            if ("address" in json_data.keys() and
                            json_data.get("address") not in LOCAL_HOST_VALUES):
                self.expected_keys = ["address", "port", "username", "password"]
                response, status_code = self.check_request_keys(json_data)
                if status_code != self.success:
                    return self.report_error(status_code, response)
        except TypeError:
            return self.report_error(400, "Failed to verify connectivity parameters")
        return self.report_success()

    def post(self):
        '''
        Post rest - receive connectivity parameters and update in backend
        '''
        if request.json:
            json_data = request.get_json(force=True)
            response, status_code = self.parse_request(json_data)
            if status_code != self.success:
                return response, status_code
            cv_address = json_data.get("address")
            cv_port = json_data.get("port", CABLE_VALIDATION_REQUEST_PORT)
            cv_username = json_data.get("username")
            cv_password = json_data.get("password")
            if cv_address not in LOCAL_HOST_VALUES: # localhost - cv plugin is running on localhost
                if not update_cv_credentials(self.cv_credentials_path, cv_address,
                                                      cv_username, cv_password):
                    return self.report_error(400, "Failed to update credentials file")
            try:
                update_cv_host_in_config_file(UFMResource.config_file_name,
                                                            cv_address, cv_port)
            except Exception as e:
                logging.error("Failed to update config file with cable validation host name %s: %s" % (cv_address, e))
                return self.report_error(400, "Failed to update config file with cable validation host name")
            return self.report_success()
        else:
            return self.report_error(400, "Action parameters not received")


class MergerDeployConfig(UFMResource):
    def __init__(self):
        super().__init__()

class MergerMergeReportId(UFMResource):
    def __init__(self):
        super().__init__()

class MergerDummyTest(UFMResource):
    def get(self):
        logging.info("GET /plugin/ndt/merger_dummy_test")
        print("Hello from dummy resource!", flush=True)
        if not check_boundary_port_state():
            error_status_code = 400
            error_response = "Failure: boundary ports state was not changed by OpenSM. No topology changes deployed."
            logging.error(error_response)
            return self.report_error(error_status_code, error_response)
        else:
            return self.report_success()

    def post(self):
        logging.info("POST /plugin/ndt/merger_dummy_test")
        return self.report_error(405, "Method is not allowed")
