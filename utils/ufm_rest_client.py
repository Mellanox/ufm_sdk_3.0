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


class MissingUFMCredentials(Exception):
    pass


class ApiErrorMessages(object):
    Missing_UFM_Credentials = "Missing UFM Authentication token or username/password"


class UfmRestConstants(object):
    UFM_API_SYSTEMS = 'resources/systems'
    UFM_API_LINKS = 'resources/links'
    UFM_API_PORTS = 'resources/ports'


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
        url = self.ws_protocol+ "://" + self.host + "/" + self.api_prefix + "/" + api_url
        headers = {}
        auth = None
        if self.client_token:
            headers["Authorization"] = "Bearer {0}".format(self.client_token)
        elif self.username and self.password:
            auth = (self.username, self.password)
        else:
            raise MissingUFMCredentials
        return url, headers, auth

    def send_request(self,url):
        try:
            url, headers, auth = self._get_ufm_request_conf(url)
            logging.info(f'Send UFM API Request, URL: {url}')
            response = requests.get(url, verify=False, headers=headers, auth=auth)
            logging.info("UFM API Request Status [" + str(response.status_code) + "], URL " + url)
            if response.raise_for_status():
                logging.error(response.raise_for_status())
            return response
        except MissingUFMCredentials as M:
            logging.error(ApiErrorMessages.Missing_UFM_Credentials)
        except Exception as e:
            logging.error(e)

    def get_systems(self):
        response = self.send_request(UfmRestConstants.UFM_API_SYSTEMS)
        return response.json()

    def get_links(self):
        response = self.send_request(UfmRestConstants.UFM_API_LINKS)
        return response.json()

    def get_ports(self):
        response = self.send_request(UfmRestConstants.UFM_API_PORTS)
        return response.json()

