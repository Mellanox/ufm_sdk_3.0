"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2020.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Anan Al-Aghbar
@date:   Sep 26, 2021
"""
import requests
import logging
import urllib3
import sys
from enum import Enum
from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MissingUFMCredentials(Exception):
    pass


class ApiErrorMessages(object):
    Missing_UFM_Credentials = "Missing UFM Authentication token or username/password"


class UfmRestConstants(object):
    UFM_API_SYSTEMS = 'resources/systems'
    # The pagination attached  in the links API as workaround for the bug https://redmine.mellanox.com/issues/2805739
    # TODO:: remove .get("data") after removing the pagination and fix the bug
    UFM_API_LINKS = 'resources/links?page_number=1&rpp=1000000000'
    UFM_API_PORTS = 'resources/ports'


class HTTPMethods(Enum):
    GET = 1
    POST = 2
    PATCH = 3
    PUT = 4
    DELETE = 5


class UfmRestClient(object):

    def __init__(self,host, ws_protocol = "https",
                 client_token = None, api_prefix = "ufmRest",
                 username = None, password = None):
        self.host = host
        self.ws_protocol = ws_protocol
        self.client_token = client_token
        self.api_prefix = api_prefix
        self.username = username
        self.password = password

    def _get_ufm_request_conf(self,api_url):
        headers = {}
        auth = None
        if self.client_token:
            headers["Authorization"] = "Basic {0}".format(self.client_token)
            self.api_prefix = "ufmRestV3"
        elif self.username and self.password:
            auth = (self.username, self.password)
        else:
            raise MissingUFMCredentials
        url = self.ws_protocol + "://" + self.host + "/" + self.api_prefix + "/" + api_url
        return url, headers, auth

    def send_request(self,url,method=HTTPMethods.GET,payload={}, files={}):
        try:
            url, headers, auth = self._get_ufm_request_conf(url)
            logging.info(f'Send UFM API Request, Method: {method} ,URL: {url}')
            if method == HTTPMethods.GET:
                response = requests.get(url, verify=False, headers=headers, auth=auth)
            elif method == HTTPMethods.POST:
                response = requests.post(url, json=payload, verify=False, headers=headers, auth=auth, files=files)
            elif method == HTTPMethods.PUT:
                response = requests.put(url, json=payload, verify=False, headers=headers, auth=auth, files=files)
            elif method == HTTPMethods.DELETE:
                response = requests.delete(url, json=payload, verify=False, headers=headers, auth=auth)
            logging.info("UFM API Request Status [" + str(response.status_code) + "], URL " + url)
            if response.raise_for_status():
                logging.error(response.raise_for_status())
            return response
        except MissingUFMCredentials as M:
            Logger.log_message(ApiErrorMessages.Missing_UFM_Credentials)
            sys.exit(1)
        except Exception as e:
            logging.error(e)
            return response

    def get_systems(self):
        response = self.send_request(UfmRestConstants.UFM_API_SYSTEMS)
        return response.json()

    def get_links(self):
        response = self.send_request(UfmRestConstants.UFM_API_LINKS)
        # the pagination attached as workaround for the bug https://redmine.mellanox.com/issues/2805739
        # TODO:: remove .get("data") after removing the pagination and fix the bug
        return response.json().get("data")

    def get_ports(self):
        response = self.send_request(UfmRestConstants.UFM_API_PORTS)
        return response.json()

