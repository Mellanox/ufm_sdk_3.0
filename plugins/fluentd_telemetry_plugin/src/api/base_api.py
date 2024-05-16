from http import HTTPStatus
from functools import partial
from flask import Flask
from flask_restful import Api
from web_service_error_messages import \
    NO_RUNNING_STREAMING_INSTANCE,\
    STREAMING_ALREADY_RUNNING

from streaming_scheduler import \
    NoRunningStreamingInstance,\
    StreamingAlreadyRunning

from api import InvalidConfRequest

# pylint: disable=no-name-in-module,import-error
from utils.json_schema_validator import ValidationError, SchemaValidationError


class BaseAPIApplication:
    """BaseAPIApplication API Flask Class Base"""

    def __init__(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.add_routes()
        self._add_error_handlers()

    def _get_error_handlers(self):
        return [
            (NoRunningStreamingInstance,
             lambda e: (NO_RUNNING_STREAMING_INSTANCE, HTTPStatus.BAD_REQUEST)),
            (StreamingAlreadyRunning,
             lambda e: (STREAMING_ALREADY_RUNNING, HTTPStatus.BAD_REQUEST)),
            (InvalidConfRequest,
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
        for code_or_exception, callback in hdlrs:
            self.app.register_error_handler(code_or_exception, callback)

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
