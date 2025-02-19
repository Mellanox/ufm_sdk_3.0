import pytest
import time
from base_functions import BaseTestTfs
from utils.json_schema_validator import validate_schema


@pytest.fixture(scope="module")
def setup_conf():
    base_test = BaseTestTfs()
    result = base_test.run_server()
    assert result > 0, "could not start the server"
    yield base_test
    base_test.stop_server()

def get_conf_test(setup_conf):
    result = setup_conf.get_conf()
    for expected_item in ["fluentd-endpoint","logs-config","streaming","meta-fields","ufm-telemetry-endpoint"]:
        assert expected_item not in result, f"expect {expected_item} in the get configuration json"

    conf_schema_path = "plugins/fluentd_telemetry_plugin/src/schemas/set_conf.schema.json"
    validate_schema(conf_schema_path, result)

def set_conf_test(setup_conf):
    conf_options = setup_conf.get_conf()
    assert conf_options["fluentd-endpoint"]["port"] != 24200
    conf_options["fluentd-endpoint"]["port"] = 24220
    setup_conf.set_conf_from_json(conf_options)
    time.sleep(5)
    conf_options = setup_conf.get_conf()
    assert conf_options["fluentd-endpoint"]["port"] == 24220
