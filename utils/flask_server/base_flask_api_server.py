#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Anan Al-Aghbar
# @date:   Sep 19, 2022
#

from flask import Flask, request
from flask_restful import Api
from http import HTTPStatus
from functools import partial
from utils.json_schema_validator import ValidationError, SchemaValidationError


class InvalidRequestError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class BaseAPIApplication:

    def __init__(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.add_routes()
        self._add_error_handlers()

    def _get_default_error_handlers(self):
        return [
            (InvalidRequestError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (ValidationError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (SchemaValidationError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (ValueError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_error_handlers(self):
        """
        Return an array of custom error handlers. Subclasses should implement
        this method if they want to add routes to their applications.
        """
        return []

    def _add_error_handlers(self):
        hdlrs = self._get_default_error_handlers() + self._get_error_handlers()
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

    def _get_request_arg(self, arg_name, def_val=None):
        """
        Returns the value of a Request Argument, if validated ok.
        :param arg_name:
        :param def_val:
        :param arg_type:
        :return:
        """
        req_arg = request.args.get(arg_name, def_val)
        if req_arg:
            self.validate_ascii(req_arg)
        return req_arg

    @staticmethod
    def validate_ascii(s):
        if isinstance(s, str):
            try:
                s.encode('ascii')
            except Exception:  # UnicodeEncodeError
                raise InvalidRequestError(
                    "Bad character encoding detected on request")
            return s
