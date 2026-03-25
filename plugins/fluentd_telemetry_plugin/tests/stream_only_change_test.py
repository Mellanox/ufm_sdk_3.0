import pytest
import time
import pandas as pd
from base_functions import BaseTestTfs

@pytest.fixture(scope="module")
def setup_conf():
    """setup the environment for the tests

    Yields:
        BaseTestTfs: base test with all the functions
    """
    base_test = BaseTestTfs()
    base_test.prepare_fluentd()
    base_test.run_simulation(max_changing=1, interval=5.0)
    result = base_test.run_server()
    assert result > 0, "could not start the server"
    yield base_test
    base_test.stop_server()
    base_test.stop_simulation()
    base_test.stop_fluentd()

def deep_check_test(setup_conf):
    time.sleep(2)
    # waiting for one message in the fluent
    telemetry_url = setup_conf.get_simulation_url()[0]
    telemetry_data = pd.read_csv(telemetry_url)

    # convert to dataframe
    plugin_data = setup_conf.extract_data_from_line(setup_conf.read_data())
    plugin_df = pd.DataFrame(plugin_data)

    # sort the dataframe so the rows will be in order
    telemetry_data = telemetry_data.sort_values(by=['node_guid', 'port_num'])
    plugin_df = plugin_df.sort_values(by=['node_guid', 'port_num'])

    assert telemetry_data.equals(plugin_df), "deep_check show that dataframes are not equal"

def get_new_data_test(setup_conf):
    previous_data = setup_conf.read_data()
    previous_df = pd.DataFrame(setup_conf.extract_data_from_line(previous_data))
    previous_df = previous_df.sort_values(by=['node_guid', 'port_num'])
    time.sleep(10)
    now_data = setup_conf.read_data()
    now_df = pd.DataFrame(setup_conf.extract_data_from_line(now_data))
    now_df = now_df.sort_values(by=['node_guid', 'port_num'])

    # checking that all is equal but the changing column
    assert previous_df.iloc[:, 6:].equals(now_df.iloc[:, 6:]),\
        "new data test: expected all the values but the changing column be the same, got difference."

    # checking that the values on the changing columns did changed.
    assert not (previous_df.iloc[:, 5] != now_df.iloc[:, 5]).all(),\
        "new data test: expected a change on changing column, got all the values are equal between the changing."
