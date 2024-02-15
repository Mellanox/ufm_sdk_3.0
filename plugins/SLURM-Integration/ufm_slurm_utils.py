#!/usr/bin/python
#
# Copyright © 2017-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

# Created on January 24, 2021
# Author: Ibrahimbar
# Author: Anas Badaha

import os
import re
import subprocess
import json
import requests
import kerberos
import ipaddress
import http.client
import logging


class Constants:
    SLURM_DEF_PATH = '/etc/slurm'
    UFM_SLURM_CONF_NAME = 'ufm_slurm.conf'
    SLURM_SERVICE_PATH = '/lib/systemd/system/slurmctld.service'
    CONF_UFM_IP = 'ufm_server'
    AUTH_TYPE = "auth_type"
    CONF_UFM_USER = 'ufm_server_user'
    CONF_UFM_PASSWORD = 'ufm_server_pass'
    CONF_TOKEN = 'token'
    CONF_PKEY_ALLOCATION = 'pkey_allocation'
    CONF_PKEY_PARAM = 'pkey'
    CONF_IP_OVER_IB_PARAM = 'ip_over_ib'
    CONF_INDEX0_PARAM = 'index0'
    CONF_SHARP_ALLOCATION = 'sharp_allocation'
    CONF_PARTIALLY_ALLOC = "partially_alloc"
    CONF_APP_RESOURCES_LIMIT = 'app_resources_limit'
    CONF_LOGFILE_NAME = 'log_file_name'
    CONF_DEBUG_MODE = 'debug_mode'
    CONF_NUM_OF_RETRIES = "num_of_retries"
    CONF_RETRY_INTERVAL = "retry_interval"
    CONF_PRINCIPAL_NAME = "principal_name"
    BASIC_AUTH = "basic_auth"
    TOKEN_AUTH = "token_auth"
    KERBEROS_AUTH = "kerberos_auth"
    CONF_FAIL_SLURM_JOB_UPON_FAILURE_PARAM = "fail_slurm_job_upon_failure"
    LS_JOB_NAME = 'slurm_job_'
    DEF_LOG_FILE = 'ufm_slurm.log'
    UFM_VER_URL = "/ufmRest/app/ufm_version"
    CREATE_SHARP_ALLOCATION_URL = "/ufmRest/app/sharp/resources"
    DELETE_SHARP_ALLOCATION_URL = "/ufmRest/app/sharp/resources/{0}"
    ADD_HOSTS_TO_PKEY_URL = "/ufmRest/resources/pkeys/hosts"
    REMOVE_HOSTS_FROM_PKEY_URL = "/ufmRest/resources/pkeys/{0}/hosts/{1}"
    UFM_NOT_RESPONDING = 'UFM server is not responding'
    UFM_NOT_AVAILABLE = 'UFM is not available'
    UFM_AUTH_ERROR = 'Could not reach UFM. Check the authentication info.'
    UFM_CONNECT_ERROR = 'Could not reach/connect to UFM.'
    UFM_ERR_PARSE_IP = 'Cannot parse UFM IP Address'
    LOG_CONNECT_UFM = 'Connecting to UFM server ... %s'
    LOG_UFM_RUNNING = 'UFM: %s is running..'
    LOG_CANNOT_UFM = 'Cannot connect to the UFM server. %s'
    LOG_CANNOT_GET_NODES = 'Could not get nodes of the job.'
    LOG_ERROR_GET_NODES = 'Error in getting nodes: %s'
    LOG_ERROR_UFM_CONNECT = 'Error in connecting to the UFM: %s'
    LOG_ERR_PROLOG = 'Error during executing ufm prolog: %s'
    LOG_ERR_EPILOG = 'Error during executing ufm epilog: %s'
    ERROR_503 = '503 service temporarily unavailable'
    ERROR_401 = 'error 401'
    NOT_FOUND = 'not found'
    ERROR = "error"
    BAD_REQUEST = "400 BAD REQUEST"
    ERROR_404 = "404 NOT FOUND"
    SBS = "ufmRest"


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

    def get_conf_parameter_value(self, conf_param_name):
        """
        This function is used to get the ufm slurm config parameter value from ufm_slurm.conf file.
        :param conf_param_name: configuration parameter name you want to get from ufm_slurm.conf file.
        :return conf_param_value: configuration parameter value in case the parameter name was found in ufm_slurm.conf file.
        :return None: in case the parameter name was not found in ufm_slurm.conf file.
        """
        conf_file_path = self.getSlurmConfFile()
        regex_pattern = fr'^(?!#)\s*{conf_param_name}\s*=\s*(\S+)'
        with open(conf_file_path, 'r') as file:
            for line in file:
                matched = re.match(regex_pattern, line)
                if matched:
                    conf_param_value = matched.group(1)
                    return conf_param_value
        return None

    def isFileExist(self, file_name):
        if os.path.exists(file_name):
            return True
        else:
            return False

    def is_debug_mode(self):
        debug_value = self.get_conf_parameter_value(Constants.CONF_DEBUG_MODE)
        if debug_value:
            if debug_value.lower() == "true":
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
        elif auth_type == Constants.KERBEROS_AUTH:
            url = resource_path.replace("ufmRest", "ufmRestKrb")
        else:
            url = resource_path
        return url

    def getServerSession(self, auth_type=None, username=None, password=None, token=None, principal_name=None):
        """
        Creating REST client session for server connection,
        after globally setting Authorization,
        Content-Type and charset for session.
        """
        session = requests.Session()
        session.verify = False
        session.headers.update({'Content-Type': 'application/json; charset=utf-8'})

        if auth_type == Constants.BASIC_AUTH:
            session.auth = (username, password)
        elif auth_type == Constants.TOKEN_AUTH:
            session.headers.update({'Authorization': 'Basic %s' % token})
        elif auth_type == Constants.KERBEROS_AUTH:
            __, krb_context = kerberos.authGSSClientInit("HTTP", principal_name)
            kerberos.authGSSClientStep(krb_context, "")
            negotiate_details = kerberos.authGSSClientResponse(krb_context)
            session.headers.update({'Authorization': 'Negotiate {0}'.format(negotiate_details)})

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

    def _create_sharp_allocation(self, ufm_server, session, auth_type, job_id, job_nodes, pkey,
                                 app_resources_limit, partially_alloc):
        resource_path = Constants.CREATE_SHARP_ALLOCATION_URL
        url = self.getUrl(resource_path, auth_type)
        if not partially_alloc:
            url = url + "?partially_alloc=false"

        body_obj = {
            "app_id": job_id,
            "hosts_names": job_nodes,
            "app_resources_limit": app_resources_limit
        }

        if pkey:
            body_obj["pkey"] = pkey

        body = json.dumps(body_obj)
        logging.info("Sending POST Request to URL:%s, with request data::: %s" % (url, body))
        return self.utils.sendPostRequestAsJSON(session, ufm_server, body, url)

    def _add_hosts_to_pkey(self, ufm_server, session, auth_type, job_nodes, pkey, ip_over_ib, index0):
        resource_path = Constants.ADD_HOSTS_TO_PKEY_URL
        url = self.getUrl(resource_path, auth_type)
        body_obj = {
            "hosts_names": job_nodes,
            "pkey": pkey,
            "ip_over_ib": ip_over_ib,
            "index0": index0
        }

        body = json.dumps(body_obj)
        logging.info("Sending POST Request to URL:%s, with request data::: %s" % (url, body))
        return self.utils.sendPostRequestAsJSON(session, ufm_server, body, url)

    def _remove_hosts_from_pkey(self, ufm_server, session, auth_type, job_nodes, pkey):
        resource_path = Constants.REMOVE_HOSTS_FROM_PKEY_URL.format(pkey, job_nodes)
        url = self.getUrl(resource_path, auth_type)

        logging.info("Sending DELETE Request to URL:%s" % url)
        return self.utils.sendDeleteRequest(session, ufm_server, url)

    def _delete_sharp_allocation(self, ufm_server, session, auth_type, job_id):

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
        ufm_manual_ip = self.utils.get_conf_parameter_value(Constants.CONF_UFM_IP)
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
