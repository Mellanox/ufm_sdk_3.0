#!/usr/bin/python
#
# Copyright © 2017-2021 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
"""
Created on January 24, 2021

@author: Ibrahimbar
@author: Anas Badaha
@copyright:
        Copyright (C) Mellanox Technologies Ltd. 2001-2021.  ALL RIGHTS RESERVED.

        This software product is a proprietary product of Mellanox Technologies Ltd.
        (the "Company") and all right, title, and interest in and to the software product,
        including all associated intellectual property rights, are and shall
        remain exclusively with the Company.

        This software product is governed by the End User License Agreement
        provided with the software product.
"""
import os
import re
import subprocess
import json
import requests
import ipaddress
import http.client
import logging


class Constants:
    SLURM_DEF_PATH = '/etc/slurm'
    UFM_SLURM_CONF_NAME = 'ufm_slurm.conf'
    SLURM_SERVICE_PATH = '/lib/systemd/system/slurmctld.service'
    CONF_UFM_IP = 'ufm_server'
    CONF_UFM_USER = 'ufm_server_user'
    CONF_UFM_PASSWORD = 'ufm_server_pass'
    CONF_PARTIALLY_ALLOC = "partially_alloc"
    CONF_PKEY_PARAM = 'pkey'
    CONF_PROTOCOL = "protocol"
    CONF_LOGFILE_NAME = 'log_file_name'
    CONF_ADD_RELATED_HOSTS = 'add_related_nics'
    CONF_DEBUG_MODE = 'debug_mode'
    CONF_TOKEN = 'token'
    CONF_CLEAN_UP = 'clean_up_ls'
    ENVIRONMENTS_MODULE = 'environments'
    SYSTEMS_MODULE = 'systems'
    SERVERS_MODULE = 'servers'
    COMPUTES_MODULE = 'computes'
    NETWORKS_MODULE = 'networks'
    NETWORKIFS_MODULE = 'network_interfaces'
    LS_JOB_NAME = 'slurm_job_'
    SLURM_ENV_NAME = 'slurm_env'
    SLURM_NETWORK = 'slurm_net'
    DEF_LOG_FILE = 'ufm_slurm.log'
    SYSTEMS_URL = "/ufmRest/resources/systems?type=host"
    SYSTEM_URL = "/ufmRest/resources/systems/%s"
    UFM_VER_URL = "/ufmRest/app/ufm_version"
    ENV_URL = "/ufmRest/resources/environments/"
    SET_NODES_TO_PKEY_URL = "/ufmRest/app/sharp/allocate_resources"
    DELETE_SHARP_ALLOCATION_URL = "/ufmRest/app/sharp/allocate_resources/{0}"
    NET_URL = "/ufmRest/resources/networks/"
    COMPUTES_URL = "/ufmRest/resources/environments/%s/logical_servers/%s/computes"
    LS_URL = "/ufmRest/resources/environments/%s/logical_servers/"
    ALL_LS_URL = "/ufmRest/resources/logical_servers"
    LS_ALLOCATE_URL = "/ufmRest/resources/environments/%s/logical_servers/%s/allocate-computes"
    NETIF_URL = "/ufmRest/resources/environments/%s/logical_servers/%s/network_interfaces"
    UFM_SLURM_CONF_NOT_EXIST = 'UFM-SLURM configuration file is not found. Check the path: %s'
    UFM_NOT_RESPONDING = 'UFM server is not responding'
    UFM_NOT_AVAILABLE = 'UFM is not available'
    UFM_AUTH_ERROR = 'Could not reach UFM. Check the authentication info.'
    UFM_CONNECT_ERROR = 'Could not reach/connect to UFM.'
    UFM_ERR_PARSE_IP = 'Cannot parse UFM IP Address'
    LOG_CONNECT_UFM = 'Connecting to UFM server ... %s'
    LOG_UFM_RUNNING = 'UFM: %s is running..'
    LOG_CANNOT_UFM = 'Cannot connect to the UFM server. %s'
    LOG_CANNOT_GET_NODES = 'Could not get nodes of the job.'
    LOG_CANNOT_GUID_NODES = 'Could not get GUID of the job nodes.'
    LOG_GUID_NOT_FOUND = ' guid is not found in UFM fabric. It could not be added to the logical server.'
    LOG_NODE_NOT_FOUND = ' is not part of the UFM fabric. It could not be added to the logical server.'
    LOG_NO_GUIDS_FOUND = 'No GUIDS of nodes are found to add.'
    LOG_CREATE_ENV = 'Creating environment %s ...'
    LOG_FAIL_CREATE_ENV = 'Failed to create environment: %s'
    LOG_ERROR_CREATE_ENV = 'Error in creating Environment %s: %s'
    LOG_CREATE_NETWORK = 'Creating private network %s ...'
    LOG_FAIL_CREATE_NETW = 'Failed to create private network: %s'
    LOG_ERROR_CREATE_NETW = 'Error in creating private network %s: %s'
    ALLOCATE_NODES = 'Allocate nodes to LS'
    LOG_ERR_ALLOCATE_NODES = 'Error in allocate nodes to LS %s: No nodes related to UFM server are found.'
    LOG_SUCCESS_ALLOCATION = 'Success. The allocation of the nodes to LS is passed'
    LOG_CREATE_LS = 'Creating logical server: %s ...'
    LOG_LS_CREATED = 'LS %s is created.'
    LOG_FAILED_CREATE_LS = 'Failed to create LS: %s.'
    LOG_ERROR_CREATE_LS = 'Error in creating LS %s: %s'
    LOG_CREATE_NWIF = 'Creating network interface for LS: %s ...'
    LOG_NWIF_CREATED = 'Network Interface for LS: %s is created.'
    LOG_FAILED_CREATE_NWIF = 'Failed to create Network Interface for LS: %s.'
    LOG_ERROR_CREATE_NWIF = 'Error in creating Network Interface for LS %s: %s'
    LOG_NOT_ALL_ALLOCATED = 'Not all the nodes are allocated to the logical server.'
    LOG_LST_NODES_NOT_ADDED = 'The following nodes are not added:'
    LOG_ERR_ALLOCATE = 'Error in allocating nodes to LS. %s'
    LOG_ERROR_GET_NODES = 'Error in getting nodes: %s'
    LOG_ERROR_UFM_CONNECT = 'Error in connecting to the UFM: %s'
    LOG_ERR_PROLOG = 'Error during executing ufm prolog: %s'
    LOG_ERR_EPILOG = 'Error during executing ufm epilog: %s'
    LOG_REMOVE_LS = 'Removing LS..'
    LOG_LS_REMOVED_SUCC = 'Logical Server: %s is removed successfully'
    LOG_LS_NOT_REMOVED = 'LS: %s is not removed'
    LOG_LS_NOT_EXIST_REMOVE = 'LS: %s is not exist to be removed'
    LOG_LS_ERR_REMOVE = 'Error in removing LS: %s'
    ERROR_503 = '503 service temporarily unavailable'
    ERROR_401 = 'error 401'
    NOT_FOUND = 'not found'
    ERROR = "error"
    BAD_REQUEST = "400 BAD REQUEST"
    ERROR_404 = "404 NOT FOUND"
    SBS = "ufmRest"
    CLEAN_LS = "Cleaning up the the existing LS of the this job nodes if any ..."
    AUTH_TYPE = "auth_type"
    BASIC_AUTH = "basic_auth"
    TOKEN_AUTH = "token_auth"


class GeneralUtils:

    def run_cmd(self, command, verbose=True):
        """
        Run Shell command.
        Direct output to subprocess.PIPE.
        Return command exit code, stdout and stderr.
        """
        proc = subprocess.Popen(command, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        stdout = stdout.decode("ascii")
        stderr = stderr.decode("ascii")
        return proc.returncode, str(stdout.strip()), str(stderr.strip())

    def getSlurmConfFile(self):
        cmd = 'cat %s | grep ConditionPathExists' % Constants.SLURM_SERVICE_PATH
        ret, path, _ = self.run_cmd(cmd)
        if ret == 0 and path:
            path = path.split('=')[1]
            return "%s/%s" % (os.path.dirname(path), Constants.UFM_SLURM_CONF_NAME)
        else:
            return "%s/%s" % (Constants.SLURM_DEF_PATH, Constants.UFM_SLURM_CONF_NAME)

    def read_conf_file(self, key):
        conf_file = self.getSlurmConfFile()
        file = open(conf_file, 'r')
        confs = file.read()
        match = re.search(r'%s=(.*)' % key, confs)
        if match:
            return match.groups()[0]
        else:
            return None

    def isFileExist(self, file_name):
        if os.path.exists(file_name):
            return True
        else:
            return False

    def getAddRelatedHosts(self):
        add_related = self.read_conf_file(Constants.CONF_ADD_RELATED_HOSTS)
        if add_related is not None:
            if "false" in add_related.lower():
                return False
        return True

    def is_debug_mode(self):
        debug_value = self.read_conf_file(Constants.CONF_DEBUG_MODE)
        if debug_value:
            if debug_value.lower() == "true":
                return True
            else:
                return False
        else:
            return False

    def is_clean_up_activated(self):
        value = self.read_conf_file(Constants.CONF_CLEAN_UP)
        if value:
            if value.lower() == "true":
                return True
            else:
                return False
        else:
            return False

    def sendPostRequest(self, session, host, body, resource_path):
        if ':' in host:
            url = 'https://[{0}]{1}'.format(host, resource_path)
        else:
            url = 'https://{0}{1}'.format(host, resource_path)
        resp = session.post(url, data=body)
        return resp

    def sendPostRequestAsJSON(self, session, host, body, resource_path):
        result = self.sendPostRequest(session, host, body, resource_path)
        try:
            result_body = json.loads(result.text)
        except:
            return result.text, result.status_code, result.reason
        return result_body, result.status_code, result.reason

    def sendGetRequest(self, session, host, resource_path,):
        if ':' in host:
            url = 'https://[{0}]{1}'.format(host, resource_path)
        else:
            url = 'https://{0}{1}'.format(host, resource_path)
        resp = session.get(url)
        return resp

    def sendGetRequestAsJSON(self, session, host, resource_path):
        result = self.sendGetRequest(session, host, resource_path)
        try:
            result_body = json.loads(result.text)
        except:
            return result.text, result.status_code, result.reason
        return result_body, result.status_code, result.reason

    def sendDeleteRequest(self, session, host, resource_path):
        if ':' in host:
            url = 'https://[{0}]{1}'.format(host, resource_path)
        else:
            url = 'https://{0}{1}'.format(host, resource_path)
        return session.delete(url)

    def sendPutRequest(self, session, host, body, resource_path):
        if ':' in host:
            url = 'https://[{0}]{1}'.format(host, resource_path)
        else:
            url = 'https://{0}{1}'.format(host, resource_path)

        return session.put(url, data=body)


class UFM:
    utils = GeneralUtils()

    def getUrl(self, resource_path, auth_type=Constants.BASIC_AUTH):
        if auth_type == Constants.TOKEN_AUTH:
            url = resource_path.replace("ufmRest", "ufmRestV3")
        else:
            url = resource_path
        return url

    def getServerSession(self, auth_type=None, username=None, password=None, token=None):
        """
        Creating REST client session for server connection,
        after globally setting Authorization,
        Content-Type and charset for session.
        """
        session = requests.Session()

        if auth_type == Constants.BASIC_AUTH:
            session.auth = (username, password)
            session.verify = False
            session.headers.update(
                {'Content-Type': 'application/json; charset=utf-8'})
        elif auth_type == Constants.TOKEN_AUTH:
            session.verify = False
            session.headers.update(
                {'Content-Type': 'application/json; charset=utf-8',
                 'Authorization': 'Basic %s' % token})

        return session

    def IsUfmRunning(self, ufm_server, session, auth_type):
        """
        Check if UFM is running on a given device.
        """
        resource_path = Constants.UFM_VER_URL
        url = self.getUrl(resource_path, auth_type)
        result = self.utils.sendGetRequest(session, ufm_server, url)
        ver = result.text

        if not ver or result.status_code != http.client.OK:
            return False, Constants.UFM_NOT_RESPONDING
        try:
            result = json.loads(ver, strict=False)
            return True, ""
        except Exception as ec:
            if Constants.ERROR_503 in ver.lower():
                return False, Constants.UFM_NOT_AVAILABLE
            elif Constants.ERROR_401 in ver.lower():
                return False, Constants.UFM_AUTH_ERROR
            else:
                return False, Constants.UFM_CONNECT_ERROR

    def _set_sharp_reservation(self, ufm_server, session, auth_type, job_id, job_nodes, pkey=None,
                               partially_alloc=True):
        resource_path = Constants.SET_NODES_TO_PKEY_URL
        url = self.getUrl(resource_path, auth_type)
        if not partially_alloc:
            url = url + "?partially_alloc=false"

        body_obj = {
            "app_id": job_id,
            "nodes": job_nodes
        }

        if pkey:
            body_obj["pkey"] = pkey

        body = json.dumps(body_obj)
        logging.info("Sending POST Request to URL:%s, with request data::: %s" % (url, body))
        return self.utils.sendPostRequestAsJSON(session, ufm_server, body, url)

    def _delete_sharp_reservation(self, ufm_server, session, auth_type, job_id):

        resource_path = Constants.DELETE_SHARP_ALLOCATION_URL.format(job_id)
        url = self.getUrl(resource_path, auth_type)
        logging.info("Sending Delete Request to URL:%s" % url)
        return self.utils.sendDeleteRequest(session, ufm_server, url)

    def IPAddressValidation(self, val):
        try:
            ipaddress.ip_address(str(val))
            return True
        except:
            return False

    def getUfmIP(self):
        ufm_manual_ip = self.utils.read_conf_file(Constants.CONF_UFM_IP)
        if ufm_manual_ip:
            if self.IPAddressValidation(ufm_manual_ip):
                return ufm_manual_ip, None
            else:
                return None, 'Error in parsing manual UFM IP, Invalid IP (%s)' % str(ufm_manual_ip)


class Integration:
    utils = GeneralUtils()
    ufm = UFM()

    def getJobNodesName(self):
        slurm_job_node_list = os.getenv('SLURM_JOB_NODELIST')
        return slurm_job_node_list
