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
    simulation_endpoint1 = ["127.0.0.1", "csv/xcset/ib_basic_debug", 9007,
                             50, "ib_basic_debug", False, 'legacy']
    simulation_endpoint2 = ["127.0.0.1", "csv/xcset/low_freq_debug", 9007,
                             50, "low_freq_debug", False, 'legacy']
    _, return_code = setup_conf.set_conf(BaseTestTfs.configure_body_conf(
        endpoints_array=[simulation_endpoint1, simulation_endpoint2]))
    assert return_code == 200

    data = setup_conf.read_data()
