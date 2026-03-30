import pytest
from base_functions import BaseTestTfs

@pytest.fixture(scope="module")
def setup_conf():
    """setup the environment for the tests

    Yields:
        BaseTestTfs: base test with all the functions
    """
    base_test = BaseTestTfs()
    base_test.prepare_fluentd()
    base_test.run_simulation()
    result = base_test.run_server()
    assert result > 0, "could not start the server"
    yield base_test
    base_test.stop_server()
    base_test.stop_simulation()
    base_test.stop_fluentd()

def verify_bulk_test(setup_conf):
    """Test bulk streaming
    """
    _, response_code = setup_conf.set_conf(setup_conf.configure_body_conf({"bulk_streaming":True}))
    assert response_code == 200
    result, message = setup_conf.verify_streaming(bulk=True)
    assert result, message

def verify_non_bulk_test(setup_conf):
    """Test not bulk streaming
    """
    _, response_code = setup_conf.set_conf(setup_conf.configure_body_conf({"bulk_streaming":False}))
    assert response_code == 200
    result, message = setup_conf.verify_streaming(bulk=False)
    assert result, message

def verify_meta_test(setup_conf):
    """Set meta information and test it
    """
    _, response_code = setup_conf.set_conf(setup_conf.configure_body_conf({"meta":
            {"alias_node_description": "node_namex",
            "alias_node_guid": "GUID",
            "add_type": "csv"}}))
    assert response_code == 200
    result, message =  setup_conf.verify_streaming(meta="node_namex",constants="csv")
    assert result, message

def info_label_test(setup_conf):
    """test the info label
    """
    result, message = setup_conf.verify_streaming(info_labels=True)
    assert result, message

def tag_msg_test(setup_conf):
    """test the tag msg after changing it.
    """
    check_tag_msg = "pytest tag check"
    _, response_code = setup_conf.set_conf(setup_conf.configure_body_conf({"tag_name":check_tag_msg}))
    assert response_code == 200
    result, message = setup_conf.verify_streaming(tag_msg=check_tag_msg)
    assert result, message
