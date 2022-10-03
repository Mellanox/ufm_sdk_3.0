import json

from http import HTTPStatus
from flask import make_response, request
from api import InvalidConfRequest
from utils.logger import LOG_LEVELS, Logger
from utils.flask_server.base_flask_api_server import BaseAPIApplication
from utils.json_schema_validator import validate_schema
from utils.utils import Utils


class SyslogStreamingConfigurationsAPI(BaseAPIApplication):

    def __init__(self, conf, syslog_forwarder):
        super(SyslogStreamingConfigurationsAPI, self).__init__()
        self.conf = conf
        self.syslog_forwarder = syslog_forwarder
        # for debugging
        # self.conf_schema_path = "plugins/ufm_syslog_streaming_plugin/src/schemas/set_conf.schema.json"
        # self.fluent_bit_conf_template_path = "../conf/fluent-bit.conf.template"

        # for production with docker
        self.conf_schema_path = "ufm_syslog_streaming_plugin/src/schemas/set_conf.schema.json"

    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get: dict(urls=["/"], methods=["GET"]),
            self.put: dict(urls=["/"], methods=["PUT"])
        }

    def _set_new_conf(self):
        new_conf = request.json
        sections = self.conf.get_conf_sections()
        for section,section_items in new_conf.items():
            if section not in sections:
                raise InvalidConfRequest(f'Invalid section: {section}')
            for section_item, value in section_items.items():
                if section_item not in dict(self.conf.get_section_items(section)).keys():
                    raise InvalidConfRequest(f'Invalid property: {section_item} in {section}')
                self.conf.set_item_value(section, section_item, value)

    def put(self):
        Logger.log_message('Updating the streaming configurations')
        # validate the new conf json
        validate_schema(self.conf_schema_path, request.json)
        # get the old ufm syslog server addr
        ohost = self.conf.get_ufm_syslog_host()
        oport = self.conf.get_ufm_syslog_port ()
        # update the saved conf values
        self._set_new_conf()
        # get the old ufm syslog server addr
        nhost = self.conf.get_ufm_syslog_host()
        nport = self.conf.get_ufm_syslog_port()
        try:
            # update the plugin conf file
            self.conf.update_config_file(self.conf.config_file)
            # check if the streaming is enabled or not
            if self.conf.get_enable_streaming_flag():
                self.syslog_forwarder.restart_forwarding(restart_ufm_syslog_server=ohost != nhost or oport != nport)
            else:
                self.syslog_forwarder.stop_forwarding()
            return make_response("set configurations has been done successfully")
        except Exception as ex:
            raise ex

    def get(self):
        try:
            with open(Utils.get_absolute_path(self.conf_schema_path)) as json_data:
                schema = json.load(json_data)
                properties = schema.get('properties', None)
                if properties is None:
                    raise Exception("Failed to get the configurations schema properties")
                conf_dict = {}
                for section in self.conf.get_conf_sections():
                    section_properties = properties.get(section, None)
                    if section_properties is None:
                        raise Exception("Failed to get the configurations schema for the section: " + section)
                    section_properties = section_properties.get('properties', None)
                    section_items = self.conf.get_section_items(section)
                    if section_properties:
                        conf_dict[section] = {}
                        for item in section_items:
                            item_type = section_properties.get(item[0], None)
                            item_value = item[1]
                            if item_type is None:
                                raise Exception(f"Failed to get the configurations schema for the item {item[0]} "
                                                f"under the section: {section}")
                            item_type = item_type.get('type', None)
                            if isinstance(item_value, str):
                                if item_type == "integer":
                                    item_value = int(item_value)
                                elif item_type == "boolean":
                                    item_value = item_value.lower() == 'true'
                            conf_dict[section][item[0]] = item_value
                    else:
                        conf_dict[section] = dict(section_items)
                return make_response(conf_dict)
        except Exception as e:
            Logger.log_message("Error occurred while getting the current streaming configurations: " + str(e), LOG_LEVELS.ERROR)