import pytest
import time
from base_functions import BaseTestTfs

@pytest.fixture(scope="module")
def setup_conf():
    """setup the environment for the tests

    Yields:
        BaseTestTfs: base test with all the functions
    """
    base_test = BaseTestTfs()
    # remove the attributes file for a clear attribute test
    base_test.run_simulation()
    result = base_test.run_server()
    assert result > 0, "could not start the server"
    yield base_test
    base_test.stop_server()
    base_test.stop_simulation()
    # remove it once again so it will not mess up other tests

def protocol_ipv4_test(setup_conf):
    """
    Test all the options using protocol ipv4
    Forward and Http protocol, includes c fluent streamer and python steamer
    """

    # testing protocol Forward
    # testing python fluent streamer
    result, message = verify_streaming_with_conf(setup_conf,"ipv4",False,False)
    assert result, message

    # testing C fluent streamer
    result, message = verify_streaming_with_conf(setup_conf,"ipv4",False,True)
    assert result, message

    # Testing HTTP protocol
    # testing python fluent streamer
    result, message = verify_streaming_with_conf(setup_conf,"ipv4",True,True)
    assert result, message

def protocol_ipv6_test(setup_conf):
    """
    Test all options using ipv6
    """
    # testing protocol Forward
    # testing python fluent streamer
    result, message = verify_streaming_with_conf(setup_conf,"ipv6",False,False)
    assert result, message

    # testing C fluent streamer
    result, message = verify_streaming_with_conf(setup_conf,"ipv6",False,True)
    assert result, message

    # Testing HTTP protocol
    # testing python fluent streamer
    result, message = verify_streaming_with_conf(setup_conf,"ipv6",True,True)
    assert result, message

def verify_streaming_with_conf(base_test:BaseTestTfs, ip_protocol="ipv4", using_http_streamer=False, using_c_fluent_streamer=False):
    """
    Verify streaming with http protocol, or with forward python/c protocol using {ip_protocol}
    """
    bind = ''
    if ip_protocol == "ipv6":
        bind = "::"
    fluent_protocol = 'forward'
    if using_http_streamer:
        fluent_protocol = 'http'
    print(f"verify stream with {fluent_protocol} protocol, on ip protocol {ip_protocol},"+
          f" with using c fluent streamer {using_c_fluent_streamer}")
    base_test.set_conf(c_fluent_streamer=using_c_fluent_streamer)
    # Forward protocol using Python forward library
    time.sleep(10)
    base_test.prepare_fluentd(fluent_protocol, bind)
    base_test.run_fluentd()
    return base_test.verify_streaming(stream=True)
