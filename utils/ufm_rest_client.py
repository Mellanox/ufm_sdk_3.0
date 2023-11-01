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
from http import HTTPStatus
from enum import Enum
from utils.logger import Logger
from requests.exceptions import ConnectionError
from utils.exception_handler import ExceptionHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MissingUFMCredentials(Exception):
    pass

class WrongUFMProtocol(Exception):
    pass

class ApiErrorMessages(object):
    Missing_UFM_Credentials = "Missing UFM Authentication token or username/password for host %s"
    Missing_UFM_Host = "Missing ufm host: %s"
    Wrong_UFM_Protocol = "Invalid protocol, please enter a valid value http or https for host %s"
    Invalid_UFM_Host = "Connection Error, please enter a valid ufm_host: %s"
    Invalid_UFM_Authentication = "Authentication Error, wrong credentials token or username/password for host %s"
    UFM_Forbidden = "you don't have permission to access %s"


class UfmRestConstants(object):
    UFM_API_SYSTEMS = 'resources/systems'
    # The pagination attached  in the links API as workaround for the bug https://redmine.mellanox.com/issues/2805739
    # TODO:: remove .get("data") after removing the pagination and fix the bug
    UFM_API_LINKS = 'resources/links?page_number=1&rpp=1000000000'
    UFM_API_PORTS = 'resources/ports'
    UFM_API_TOKEN = 'app/tokens'


class HTTPMethods(Enum):
    GET = 1
    POST = 2
    PATCH = 3
    PUT = 4
    DELETE = 5


class UfmProtocols(Enum):
    http = "http"
    https = "https"


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
        if self.ws_protocol != UfmProtocols.http.value and self.ws_protocol != UfmProtocols.https.value:
            raise WrongUFMProtocol
        url = self.ws_protocol + "://" + self.host + "/" + self.api_prefix + "/" + api_url
        return url, headers, auth

    def send_request(self,url,method=HTTPMethods.GET,payload={}, files={}, exit_on_failure=True):
        response = None
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
            response.raise_for_status()
            return response
        except MissingUFMCredentials as M:
            ExceptionHandler.handel_exception(ApiErrorMessages.Missing_UFM_Credentials % self.host, exist=exit_on_failure)
        except WrongUFMProtocol as W:
            ExceptionHandler.handel_exception(ApiErrorMessages.Wrong_UFM_Protocol % self.host, exist=exit_on_failure)
        except ConnectionError as e:
            ExceptionHandler.handel_exception(ApiErrorMessages.Invalid_UFM_Host % self.host, exist=exit_on_failure)
        except Exception as e:
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                ExceptionHandler.handel_exception(ApiErrorMessages.Invalid_UFM_Authentication % self.host, exist=exit_on_failure)
            if response.status_code == HTTPStatus.FORBIDDEN:
                ExceptionHandler.handel_exception(ApiErrorMessages.UFM_Forbidden % url)
            else:
                err = f'{e}'
                if response:
                    err += f'\n{response.text}'
                ExceptionHandler.handel_exception(err, exist=exit_on_failure)

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

    def generate_token(self):
        response = self.send_request(UfmRestConstants.UFM_API_TOKEN,
                                     HTTPMethods.POST,
                                     exit_on_failure=False)
        if response:
            return response.json().get("access_token")
        return None
