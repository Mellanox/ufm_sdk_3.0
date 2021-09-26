"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2021. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nahum Kilim
@date:   September 20, 2021
"""

import json
import os
from flask_restful import Resource

BASE_RESOURCES_DIR = "/opt/ufm/ufm_web_sim/src/ufm_sim/resources"


def read_json_file(file_name):
    try:
        file_path = os.path.join(BASE_RESOURCES_DIR, file_name)
        with open(file_path) as pfile:
            data = json.load(pfile)
    except Exception as ex:
        print("Exception, %s" % ex)
        data = {}
    return data


class UFMResource(Resource):
    file_name = ""

    def get(self):
        return read_json_file(self.file_name)

class Command(UFMResource):
    def get(self):
        return read_json_file(self.file_name)
 

class Systems(UFMResource):
    file_name = "systems.json"


class Links(UFMResource):
    file_name = "links.json"


class Pkeys(UFMResource):
    file_name = "pkeys.json"


class Ports(UFMResource):
    file_name = "ports.json"


class PkeysLastUpdated(UFMResource):
    file_name = "pkeys_last_updated.json"


class Modules(UFMResource):
    file_name = "modules.json"


class UfmVersion(UFMResource):
    file_name = "ufm_version.json"
