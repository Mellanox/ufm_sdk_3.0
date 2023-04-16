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

from flask import Flask
from flask_restful import Api
from http import HTTPStatus
from functools import partial
import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(os.path.dirname(parent))
from utils.json_schema_validator import ValidationError, SchemaValidationError

from api import InvalidRequest


class BaseAPIApplication:

    def __init__(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.add_routes()
        self._add_error_handlers()

    def _get_error_handlers(self):
        return [
            (InvalidRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (ValidationError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (SchemaValidationError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (ValueError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
        ]

    def _add_error_handlers(self):
        hdlrs = self._get_error_handlers()
        for code_or_exception, f in hdlrs:
            self.app.register_error_handler(code_or_exception, f)

    @property
    def application(self):
        """read-only property for the application instance."""
        return self.app

    def _get_routes(self):
        """Return a mapping between URLs to their
        view functions / endpoints. Subclasses should implement
        this method if they want to add routes to their applications."""
        return {}

    def _check_rest_api_handlers(self, endpoint, *args, **kwargs):

        return endpoint(*args, **kwargs)

    def add_routes(self):
        """Route URLs to their view functions."""
        routes = self._get_routes()
        for endpoint, route in routes.items():
            urls = route.get('urls', [])
            methods = route.get('methods')
            func = partial(self._check_rest_api_handlers, endpoint)
            func.__name__ = endpoint.__name__
            for url in urls:
                self.app.add_url_rule(
                    url,
                    view_func=func,
                    methods=methods,
                    strict_slashes=False)
            auth_level = route.get('auth_level', 0)
            self.app.config.setdefault(
                'auth_level', {})[
                endpoint.__func__.__name__] = auth_level
