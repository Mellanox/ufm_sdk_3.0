#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

from flask import make_response, request
from api import InvalidRequest
from api.base_api import BaseAPIApplication
from utils.json_schema_validator import validate_schema


class PortsStateAPI(BaseAPIApplication):

    def __init__(self, isolation_mgr):
        super(PortsStateAPI, self).__init__()

        self.set_state_schema_path = "/opt/ufm/ufm_plugin_pdr_deterministic/ufm_sim_web_service/schemas/set_port_state.schema.json"
        self.isolation_mgr = isolation_mgr

    def _get_routes(self):
        return {
            self.post: dict(urls=["/"], methods=["POST"])
        }

    def post(self):
        # validate the new conf json
        validate_schema(self.set_state_schema_path, request.json)
        #ports_states = dict(json.loads(request.json))
        self.isolation_mgr.set_ports_as_treated(request.json)
        return make_response("Updated successfully ports' states")
    