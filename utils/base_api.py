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
@date:   Sep 11, 2022
"""

from flask import Flask, request
from flask_restful import Api
from functools import partial
from utils.ufm_rest_client import ApiErrorMessages


class InvalidRequestError(Exception):
    pass


class BaseAPIApplication:

    def __init__(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.add_routes()
        self._add_error_handlers()

    def _get_error_handlers(self):
        """Return a list of pairs: Exception classes
                or status codes associated with their endpoint functions that
                handle the error/exception and create the
                appropriate view. Subclasses should implement this
                method if they want to add error handlers to their
                application."""
        return []

    def _add_error_handlers(self):
        handlers = self._get_error_handlers()
        for code_or_exception, f in handlers:
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

    def _getRequestArg(self, arg_name, def_val=None):
        """
        Returns the value of a Request Argument, if validated ok.
        :param arg_name:
        :param def_val:
        :param arg_type:
        :return:
        """
        req_arg = request.args.get(arg_name, def_val)
        if req_arg:
            self.validateASCII(req_arg)
        return req_arg

    @staticmethod
    def validateASCII(s):
        if isinstance(s, str):
            try:
                s.encode('ascii')
            except Exception:  # UnicodeEncodeError
                raise InvalidRequestError(
                    ApiErrorMessages.BAD_CHARACTER_ENCODING_DETECTED)
            return s
