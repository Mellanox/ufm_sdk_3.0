import json
import ast
import logging
from jsonschema import validate, FormatChecker
from jsonschema.exceptions import ValidationError, SchemaError



class BaseSchemaValidationError(Exception):
    pass


class SchemaValidationError(BaseSchemaValidationError):
    pass


class ValidatorSchemaConstants(object):

    SCHEMA_PROPERTIES_SECTION = "properties"
    SCHEMA_REQUIRED_SECTION = "required"
    SCHEMA_ITEMS_SECTION = "items"
    SCHEMA_ERROR_MSG = "err_message"
    SCHEMA_MESSAGES = "messages"
    SCHEMA_ERR_FMT = "err_fmt"


def validate_schema(schema_path, data):
    data = clean_unicode(data)
    if schema_path:
        try:
            with open(schema_path) as json_data:
                schema = json.load(json_data)
                check_structures = (
                            ValidatorSchemaConstants.SCHEMA_PROPERTIES_SECTION,
                            ValidatorSchemaConstants.SCHEMA_REQUIRED_SECTION)
                for struct_name in check_structures:
                    struct_val = schema.get(struct_name)
                    if struct_val:
                        schema[struct_name] = clean_unicode(struct_val)
                    else:
                        items = schema.get(
                                ValidatorSchemaConstants.SCHEMA_ITEMS_SECTION)
                        if items:
                            struct_val = items.get(struct_name)
                            if struct_val:
                                schema[
                                ValidatorSchemaConstants.SCHEMA_ITEMS_SECTION][
                                        struct_name] = clean_unicode(struct_val)
                validate(data, schema, format_checker=FormatChecker())
        # In case there's a problem with the schema's format,
        # we will raise an exception.
        # This error can occur when someone changed the schema.
        except SchemaError as e:
            raise Exception(str(e))
        # In case an attribute fails to pass the schema's validations,
        # jsonschema will raise an exception
        except ValidationError as e:
            # "err_message" is a custom attribute we created to raise in cases
            # where the default error message isn't clear enough.
            # For a detailed example, please refer to the file
            # "create_network.schema.json"
            message = e.schema.get(ValidatorSchemaConstants.SCHEMA_ERROR_MSG)
            if not message:
                # "err_fmt" is another custom attribute we created to raise
                # in cases where the default error message isn't clear enough.
                # The value of this attribute should be a string, and can
                # include the attribute's name and value inside.
                # For example:
                # "err_fmt": "%(attr)s: %(val)s Should be a valid IP address"
                message = e.schema.get(ValidatorSchemaConstants.SCHEMA_ERR_FMT)
                # If e.path is not empty, the value of e.path is a deque containing
                # the invalid attribute's name
                attr_name = e.path.pop() if e.path else ""

                if message:
                    message = message % dict(attr=attr_name, val=e.instance)
                else:  # no 'err_message' neither 'err_fmt' attribute in the json schema
                    if attr_name:
                        message = "Invalid attribute %s: %s" %\
                            (attr_name, e.message)
                    else:
                        messages = e.schema.get(ValidatorSchemaConstants.SCHEMA_MESSAGES)
                        if messages and e.validator and messages[e.validator]:
                            message = messages[e.validator]
                        else:
                            message = e.message

                if message:
                    logging.error(message)

            raise SchemaValidationError(message)

        except Exception as e:  # bug? with the schema, not the payload
            logging.error(
                "Failed to load json schema: %s, check json format, %s" %\
                    (schema_path, e.message))
            raise Exception("Failed to validate request")
    else:
        logging.error("json schema isn't provided")


def clean_unicode(data):
    try:
        data = ast.literal_eval(json.dumps(data))
    except:
        pass
    return data
