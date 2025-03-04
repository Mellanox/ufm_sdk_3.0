import pytest
from base_functions import BaseTestTfs

@pytest.fixture(scope="module")
def setup_conf():
    """setup the environment for the tests

    Yields:
        BaseTestTfs: base test with all the functions
    """
    base_test = BaseTestTfs()
    # remove the attributes file for a clear attribute test
    base_test.prepare_fluentd()
    base_test.run_simulation(simulation_paths=['/csv/xcset/ib_basic_debug', '/csv/xcset/low_freq_debug'])
    result = base_test.run_server()
    assert result > 0, "could not start the server"
    yield base_test
    base_test.stop_server()
    base_test.stop_simulation()
    base_test.stop_fluentd()
    # remove it once again so it will not mess up other tests

def set_multi_endpoint_test(setup_conf):
    """
       Test multi telemetry with the same url
    """
    constants = ("127.0.0.1", "csv/xcset/ib_basic_debug", 10, 50, "test", True, 'legacy')
    for amount in range(2,10):
        endpoint_array = [list(constants) for _ in range(amount)]
        _, return_code = setup_conf.set_conf(BaseTestTfs.configure_body_conf(endpoints_array=endpoint_array))
        assert return_code == 200

def check_data_test(setup_conf):
    """
        Test getting data from 2 endpoints at the same time
    """
    tag_msg1 = "ib_basic_debug"
    tag_msg2 = "low_freq_debug"
    simulation_endpoint1 = ["127.0.0.1", "csv/xcset/ib_basic_debug", 9007,
                             50, tag_msg1, False, 'legacy']
    simulation_endpoint2 = ["127.0.0.1", "csv/xcset/low_freq_debug", 9007,
                             50, tag_msg2, False, 'legacy']
    _, return_code = setup_conf.set_conf(BaseTestTfs.configure_body_conf(
        endpoints_array=[simulation_endpoint1, simulation_endpoint2]))
    assert return_code == 200

    data = setup_conf.read_data()
    tag_msg_in_data = [False,False]
    for msg in data.splitlines():
        if tag_msg1 in msg:
            tag_msg_in_data[0] = True
        if tag_msg2 in msg:
            tag_msg_in_data[1] = True
    
    assert tag_msg_in_data[0] and tag_msg_in_data[1],\
        f"Cannot read the tag message from both endpoints: {tag_msg1}:{tag_msg_in_data[0]},"\
            +f"{tag_msg2}:{tag_msg_in_data[1]}."
