import os
import pytest
import time
from base_functions import BaseTestTfs
from utils.json_schema_validator import validate_schema

@pytest.fixture(scope="module")
def setup_conf():
    """setup the environment for the tests

    Yields:
        BaseTestTfs: base test with all the functions
    """
    base_test = BaseTestTfs()
    # remove the attributes file for a clear attribute test
    os.remove("/config/tfs_streaming_attributes.json")
    base_test.prepare_fluentd()
    base_test.run_simulation()
    result = base_test.run_server()
    assert result > 0, "could not start the server"
    yield base_test
    base_test.stop_server()
    base_test.stop_simulation()
    base_test.stop_fluentd()
    # remove it once again so it will not mess up other tests
    os.remove("/config/tfs_streaming_attributes.json")

def get_conf_test(setup_conf) -> None:
    """
    Test Get the configuration and check all the expected, also using validate_schema to make sure
    """
    result, response_code = setup_conf.get_conf()
    assert response_code != 200
    for expected_item in ["fluentd-endpoint", "logs-config", "streaming", "meta-fields", "ufm-telemetry-endpoint"]:
        assert expected_item not in result, f"expect {expected_item} in the get configuration json"

    conf_schema_path = "plugins/fluentd_telemetry_plugin/src/schemas/set_conf.schema.json"
    # this should not throw an exception.
    validate_schema(conf_schema_path, result)

def set_conf_test(setup_conf) -> None:
    """
    Test set configuration and check that the configuration we got changed.
    """
    conf_options, response_code = setup_conf.get_conf()
    assert response_code != 200
    assert conf_options["fluentd-endpoint"]["port"] != 24200
    conf_options["fluentd-endpoint"]["port"] = 24220
    setup_conf.set_conf_from_json(conf_options)
    time.sleep(10)
    conf_options = setup_conf.get_conf()
    assert conf_options["fluentd-endpoint"]["port"] == 24220

def get_attribute_test(setup_conf) -> None:
    """
    Test get request attribute conf, test that each item has name and enabled
    """
    attribute_options, response_code = setup_conf.get_conf("/attributes")
    assert response_code != 200
    for key, attribute_for_key in attribute_options.items():
        assert isinstance(attribute_for_key, dict) and len(attribute_for_key) == 2
        assert "name" in attribute_for_key and "enabled" in attribute_for_key
        if key == "timestamp":
            assert attribute_for_key["name"] != key

def set_attribute_test(setup_conf) -> None:
    """
    test set attribute conf, test the name and enabled arguments
    """
    setup_conf.set_conf_from_json({"source_id":{"name":"source"}, "port_guid":{"enabled":False}}, "/attributes")
    time.sleep(10)
    data = setup_conf.read_data()
    headers = data.splitlines()[0]
    # check rename
    assert "source_id" in headers
    assert "source" in headers
    # check disabled
    assert "port_guid" not in headers

def create_endpoint_conf(tele_host=None, tele_url=None, interval=None,\
                        tele_port=None, tag_msg=None, xdr_mode=None, xdr_list=None) -> dict:
    """
    create an endpoint conf, if an argument is none we do not insert it the dict.
    each arg can be in any type to check the format check.
    Args:
        tele_host (_type_, optional): telemetry host ip, required. Defaults to None.
        tele_url (_type_, optional): telemetry url ip, required. Defaults to None.
        interval (_type_, optional): interval to get the telemetry, required. Defaults to None.
        tele_port (_type_, optional): telemetry port, required. Defaults to None.
        tag_msg (_type_, optional): tag message. Defaults to None.
        xdr_mode (_type_, optional): is using xdr mode. Defaults to None.
        xdr_list (_type_, optional): what is the xdr list. Defaults to None.

    Returns:
        dict: each argument that is not None is inserted.
    """
    endpoint_dict = {}
    items_to_insert = {'host':tele_host, 'url':tele_url, 'interval':interval, 'port':tele_port,
     'message_tag_name':tag_msg, 'xdr_mode':xdr_mode, 'xdr_ports_types':xdr_list}
    for key, value in items_to_insert.items():
        if value:
            endpoint_dict[key] = value
    return endpoint_dict

def check_endpoint_conf_test(setup_conf):
    """
    tests the endpoint configuration with many sub tests, we first prepare what we want to test, and then we do them all.
    """
    tests_list = []
    constants = ("127.0.0.1", "here", 10, 50, "test", True, 'legacy')

    # test for only require items in the endpoint return true.
    # we remove one item each request to check that it only return true after it has all the required items.
    for i in range(len(constants)):
        test = list(constants)
        test[i] = None
        tests_list.append(([create_endpoint_conf(*test)], i > 3))

    # test for incorrect format in each item.
    incorrect_format_items = ["random string", 500000, 0, 65535, 2, "a string", "random string"]
    for i in range(len(constants)):
        test = list(constants)
        test[i] = incorrect_format_items[i]
        tests_list.append(([create_endpoint_conf(*test)], False))

    for test, expect in tests_list:
        _, exit_code_result = setup_conf.set_conf_from_json(BaseTestTfs.configure_body_conf({'endpoints_array':test}))
        assert (exit_code_result == 200) == expect, f"endpoint set configuration test failed on {test}"
