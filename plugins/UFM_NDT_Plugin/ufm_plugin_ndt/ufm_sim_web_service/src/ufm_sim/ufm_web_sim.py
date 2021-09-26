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

from flask import Flask
from flask_restful import Api

from ufm_sim.resources import Systems, Links, Pkeys, Ports, PkeysLastUpdated, Modules, UfmVersion, Command


class UFMWebSim:

    def __init__(self):
        # Create routes
        self.port_number = 8980
        self.app = Flask(__name__)
        api = Api(self.app)

        apis = {
            Command: "/ufmRest/resources/command",
            Systems: "/ufmRest/resources/systems",
            Links: "/ufmRest/resources/links",
            Pkeys: "/ufmRest/resources/pkeys",
            Ports: "/ufmRest/resources/ports",
            PkeysLastUpdated: "/ufmRest/resources/pkeys/last_updated",
            Modules: "/ufmRest/resources/modules",
            UfmVersion: "/ufmRest/app/ufm_version"
        }
        for resource, path in apis.items():
            api.add_resource(resource, path)

    def run(self):
        self.app.run(host='0.0.0.0', port=self.port_number, debug=True)

    def stop(self):
        pass
