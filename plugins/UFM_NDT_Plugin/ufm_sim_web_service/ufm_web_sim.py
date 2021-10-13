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

from resources import Compare, Ndts, Reports, ReportId, UploadMetadata, Delete


class UFMWebSim:

    def __init__(self):
        # Create routes
        self.port_number = 8980
        self.app = Flask(__name__)
        api = Api(self.app)

        apis = {
            Compare: "/ufmRestV2/plugin/ndt/compare",
            Ndts: "/ufmRestV2/plugin/ndt/list",
            Reports: "/ufmRestV2/plugin/ndt/reports",
            Delete: "/ufmRestV2/plugin/ndt/delete",
            UploadMetadata: "/ufmRestV2/plugin/ndt/upload_metadata",
            ReportId: "/ufmRestV2/plugin/ndt/reports/<report_id>",
        }
        for resource, path in apis.items():
            api.add_resource(resource, path)

    def run(self):
        self.app.run(host='0.0.0.0', port=self.port_number, debug=True)

    async def stop(self):
        pass
