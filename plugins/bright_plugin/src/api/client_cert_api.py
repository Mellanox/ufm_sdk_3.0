"""
@copyright:
    Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   Sep 26, 2022
"""
import os
from flask import request, make_response, jsonify

from mgr.bright_mgr import BrightConstants
from utils.base_api import BaseAPIApplication


class ClientCertificateAPI(BaseAPIApplication):
    ALLOWED_EXTENSIONS = {'pem', 'key'}

    def __init__(self):
        super(ClientCertificateAPI, self).__init__()

    def _get_routes(self):
        return {
            self.post: dict(urls=["/"], methods=["POST"])
        }

    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def post(self):
        # check if the post request has the file part
        if 'file' not in request.files:
            raise Exception("Failed to get the configurations schema properties")
        file = request.files['file']
        if file.filename == '':
            raise Exception('No selected file')
        if file and self.allowed_file(file.filename):
            file.save(os.path.join(BrightConstants.CERT_DIR, f'admin.{file.filename.rsplit(".", 1)[1].lower()}'))
            return make_response(jsonify("client certificate file has been updated successfully"))
