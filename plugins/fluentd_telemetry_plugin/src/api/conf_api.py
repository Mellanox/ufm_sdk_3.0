import re
import json
import logging
from http import HTTPStatus
from flask import make_response, request
from api import InvalidConfRequest
from api.base_api import BaseAPIApplication
from streamer import UFMTelemetryStreaming, InvalidConfSetting
from streaming_scheduler import StreamingScheduler

# pylint: disable=no-name-in-module,import-error
from utils.json_schema_validator import validate_schema
from utils.utils import Utils


class StreamingConfigurationsAPI(BaseAPIApplication):
    """StreamingConfigurationsAPI class"""

    def __init__(self, conf):
        super(StreamingConfigurationsAPI, self).__init__()  # pylint: disable=super-with-arguments
        self.conf = conf
        self.scheduler = StreamingScheduler()
        self.streamer = UFMTelemetryStreaming()
        #to debug
        # self.conf_schema_path = "plugins/fluentd_telemetry_plugin/src/schemas/set_conf.schema.json"
        # self.conf_attributes_schema_path = "plugins/fluentd_telemetry_plugin/src/schemas/set_attributes.schema.json"

        self.conf_schema_path = "fluentd_telemetry_plugin/src/schemas/set_conf.schema.json"
        self.conf_attributes_schema_path = "fluentd_telemetry_plugin/src/schemas/set_attributes.schema.json"

    def _get_routes(self):
        return {
            self.get: {'urls': ["/"], 'methods': ["GET"]},
            self.post: {'urls': ["/"], 'methods': ["POST"]},
            self.get_streaming_attributes: {'urls': ["/attributes"], 'methods': ["GET"]},
            self.update_streaming_attributes: {'urls': ["/attributes"], 'methods': ["POST"]}
        }

    def _set_new_conf(self): # pylint: disable=too-many-branches
        new_conf = request.json
        sections = self.conf.get_conf_sections()
        for section, section_items in new_conf.items():
            if section not in sections:
                raise InvalidConfRequest(f'Invalid section: {section}')
            if section == self.conf.META_FIELDS_SECTION:
                #special logic for the meta-fields section because it contains dynamic options
                #current options meta-fields should be overwritten with the new options
                self.conf.clear_section_items(section)
                for section_item, value in section_items.items():
                    if not re.match(r'(alias_|add_).*$', section_item):
                        raise InvalidConfRequest(f'Invalid property: {section_item} in {section}; '
                                                 f'the meta-field key should be with format '
                                                 f'"alias_[[key]]" for aliases or "add_[[key]]" for constants pairs')
                    self.conf.set_item_value(section, section_item, value)

            elif section == self.conf.UFM_TELEMETRY_ENDPOINT_SECTION:
                # in this section the items will be an array of telemetry endpoint objects (host,port,url)
                # and we should translate them into comma separated string
                endpoint_obj_keys = dict(self.conf.get_section_items(section)).keys()
                new_section_data = {}
                for endpoint in section_items:
                    for endpoint_item in endpoint_obj_keys:
                        endpoint_item_value = endpoint.get(endpoint_item,"")
                        if endpoint_item == self.conf.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE:
                            endpoint_item_value = self.conf.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE_SPLITTER.join(endpoint_item_value)
                        new_section_data[endpoint_item] = f'{new_section_data.get(endpoint_item, "")},{endpoint_item_value}'
                for endpoint_item in endpoint_obj_keys:
                    self.conf.set_item_value(section, endpoint_item, new_section_data.get(endpoint_item)[1:].strip())
            else:
                for section_item, value in section_items.items():
                    if section_item not in dict(self.conf.get_section_items(section)).keys():
                        raise InvalidConfRequest(f'Invalid property: {section_item} in {section}')
                    self.conf.set_item_value(section, section_item, value)

    def _validate_required_configurations_on_enable(self):
        # just checking the required attributes
        # if one of the attributes below was missing it will throw an exception
        return self.conf.get_fluentd_host()

    def post(self):
        # validate the new conf json
        validate_schema(self.conf_schema_path, request.json)
        self._set_new_conf()
        try:
            if self.conf.get_enable_streaming_flag():
                self._validate_required_configurations_on_enable()
                self.scheduler.stop_streaming()
                self.scheduler.start_streaming(update_attributes=True)
            else:
                self.scheduler.stop_streaming()

            self.conf.update_config_file(self.conf.config_file)
            return make_response("set configurations has been done successfully")
        except ValueError as ex:
            self.conf.set_item_value(self.conf.STREAMING_SECTION, self.conf.STREAMING_SECTION_ENABLED, False)
            self.conf.update_config_file(self.conf.config_file)
            raise ex

    def get(self):  # pylint: disable=too-many-locals, too-many-branches
        try:
            with open(Utils.get_absolute_path(self.conf_schema_path), encoding='utf-8') as json_data:
                schema = json.load(json_data)
                properties = schema.get('properties', None)
                if properties is None:
                    raise InvalidConfRequest("Failed to get the configurations schema properties")
                conf_dict = {}
                for section in self.conf.get_conf_sections():  # pylint: disable=too-many-nested-blocks
                    section_properties = properties.get(section, None)
                    if section_properties is None:
                        raise InvalidConfRequest("Failed to get the configurations schema for the section: " + section)
                    section_type = section_properties.get("type")
                    section_items = self.conf.get_section_items(section)
                    if section_type == "array":
                        # in case the section_type is array, we need to collect
                        # the array elements from the saved comma separated strings
                        section_value_splitter = section_properties.get('splitter', ',')
                        section_properties = section_properties.get('items', {}).get("properties", None)
                        if section_properties:
                            conf_dict[section] = []
                            for item_key, item_value in section_items:
                                item = section_properties.get(item_key, None)
                                if item is None:
                                    raise InvalidConfRequest(f'Failed to get the configurations schema for the item {item_key} '
                                                             f'under the section: {section}')
                                item_type = item.get('type', None)
                                item_value_splitter = item.get('splitter', ';')
                                item_values = item_value.split(section_value_splitter)
                                for i, value in enumerate(item_values):
                                    try:
                                        arr_element_obj = conf_dict[section][i]
                                    except IndexError:
                                        arr_element_obj = {}
                                        conf_dict[section].append(arr_element_obj)
                                    arr_element_obj[item_key] = Utils.convert_str_to_type(value, item_type, item_value_splitter)
                                    conf_dict[section][i] = arr_element_obj
                    elif section_type == "object":
                        section_properties = section_properties.get('properties', None)
                        if section_properties:
                            conf_dict[section] = {}
                            for item_key, item_value in section_items:
                                item_type = section_properties.get(item_key, None)
                                if item_type is None:
                                    raise InvalidConfRequest(f'Failed to get the configurations schema for the item {item_key} '
                                                             f'under the section: {section}')
                                item_type = item_type.get('type', None)
                                item_value = Utils.convert_str_to_type(item_value, item_type)
                                conf_dict[section][item_key] = item_value
                        else:
                            conf_dict[section] = dict(section_items)
                    else:
                        raise InvalidConfRequest(f'Failed to get the configurations, unsupported type '
                                                 f'{section_type}: for the section: {section}')
                return make_response(conf_dict)
        except InvalidConfRequest as ex:
            err_msg = f"Error occurred while getting the current streaming configurations: {str(ex)}"
            logging.error(err_msg)
            return make_response(err_msg, HTTPStatus.INTERNAL_SERVER_ERROR)

    def get_streaming_attributes(self):
        return make_response(self.streamer.attributes_mngr.streaming_attributes)

    def update_streaming_attributes(self):
        payload = request.json
        # validate the new payload
        validate_schema(self.conf_attributes_schema_path, payload)
        for key,value in payload.items():
            current_attr_obj = self.streamer.attributes_mngr.streaming_attributes.get(key, None)
            if current_attr_obj is None:
                raise InvalidConfRequest(f'The streaming attribute : {key} not found in the attributes list')
            self.streamer.attributes_mngr.streaming_attributes[key] = value
        try:
            self.streamer.attributes_mngr.update_saved_streaming_attributes()
        except InvalidConfSetting as error:
            raise InvalidConfRequest(str(error)) from error
        return make_response('set streaming attributes has been done successfully')
