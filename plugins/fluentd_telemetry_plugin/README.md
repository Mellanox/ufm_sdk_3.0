UFM Telemetry endpoint stream To Fluentd endpoint (TFS)
--------------------------------------------------------


This plugin is used to extract UFM telemetry counters via [Prometheus](https://prometheus.io/) metrics and stream it via [fluentd](https://www.fluentd.org/) protocol to telemetry console

Overview
--------------------------------------------------------

NVIDIA UFM Telemetry platform provides network validation tools to monitor network performance and conditions, capturing and streaming rich real-time network telemetry information, application workload usage to an on-premise or cloud-based database for further analysis.
As a fabric manager, the UFM Telemetry holds a real-time network telemetry information of the network topology. This information should be reflected, over time (as it can change with time) towards telemetry console. In order to do so, we present stream the UFM Telemetry data To the [Fluentd](https://www.fluentd.org/) plugin



Plugin Deployment
--------------------------------------------------------

### To deploy the plugin on UFM-SDN Appliance:

- Login as admin
- Run 


    > enable
    
    > config terminal

- Make sure that UFM is running


    > show ufm status
- if UFM is down then run it

    > ufm start
  
- Make sure docker is running
  
    > no docker shutdown
  
- Load the latest plugin container
  - In case of HA, load the plugin on the standby node as well;
  - if your appliance is connected to the internet, you could simply run:
    > docker pull mellanox/ufm-plugin-tfs
  - if your appliance is not connected to the internet, you need to load the image offline 
    - Use a machine that is connected to the internet to save the docker image 
      > docker save mellanox/ufm-plugin-tfs:latest | gzip > ufm-plugin-tfs.tar.gz
    - Move the file to scp shared location that is accessible to the appliance 
    - Fetch the image to the appliance 
      > image fetch scp://user@hostname/path-to-file/ufm-plugin-tfs.tar.gz
    - Load the image
      > docker load ufm-plugin-tfs.tar.gz
- Enable & start the plugin 

    > ufm plugin tfs add
    
    
-	Check that plugin is up and running with

    > show ufm plugin


### To deploy the plugin on UFM Docker container:
  - Load the latest plugin container
      - In case of HA, load the plugin on the standby node as well;
      - if your machine is connected to the internet, you could simply run:
        > docker pull mellanox/ufm-plugin-tfs
      - if your appliance is not connected to the internet, you need to load the image offline 
        - Use a machine that is connected to the internet to save the docker image 
          > docker save mellanox/ufm-plugin-tfs:latest | gzip > ufm-plugin-tfs.tar.gz
        - Move the file to some shared location that is accessible to the UFM machine 
        - Load the image to UFM machine
          > docker load < /[some-shared-location]/ufm-plugin-tfs.tar.gz
        
- Enable & start the plugin
    > docker exec ufm /opt/ufm/scripts/manage_ufm_plugins.sh add -p tfs  


- Check that plugin is up and running with
    
    
    > docker exec ufm /opt/ufm/scripts/manage_ufm_plugins.sh show


### To deploy the plugin with UFM Enterprise (SA or HA):
- Install the latest version of UFM.
 
- Load the latest plugin container
  - In case of HA, load the plugin on the standby node as well;
  - if your machine is connected to the internet, you could simply run:
    > docker pull mellanox/ufm-plugin-tfs
  - if your appliance is not connected to the internet, you need to load the image offline 
    - Use a machine that is connected to the internet to save the docker image 
      > docker save mellanox/ufm-plugin-tfs:latest | gzip > ufm-plugin-tfs.tar.gz
    - Move the file to some shared location that is accessible to the UFM machine 
    - Load the image to UFM machine
      > docker load < /[some-shared-location]/ufm-plugin-tfs.tar.gz
      
- To enable & start the plugin, run :

    > /opt/ufm/scripts/manage_ufm_plugins.sh add -p tfs
  
- Check that plugin is up and running with
 
    >docker ps;

Log file tfs.log is located in /opt/ufm/files/log/plugins/tfs/tfs.log

FluentdD Deployment configurations
--------------------------------------------------------

- Pull the [Fluentd Docker](https://hub.docker.com/r/fluent/fluentd/) by running:
 
 
    > docker pull fluent/fluentd
    
- Run the Fluentd docker by running:

    
    > docker run -ti --rm --network host -v /tmp/fluentd:/fluentd/etc fluentd -c /fluentd/etc/fluentd.conf -v

* We provide [fluentd.conf](conf/fluentd.conf) as a fluentd configurations sample.
* In case of enabling [streaming.compressed_streaming](conf/fluentd_telemetry_plugin.cfg#L15) the source type should be **http**; otherwise the type should be **forward**

IPv6 configurations
--------------------------------------------------------
To run the plugin via the IPv6, please make sure that you are running the telemetry & fluentd endpoints on the IPv6 interfaces:
* For FluentD configurations, please replace [fluentd host address](conf/fluentd.conf#3) (bind 0.0.0.0) with (bind ::)
* For UFM telemetry configurations:
    1. In case you are running the UFM telemetry within the UFM Enterprise, please make sure to set manual_config True under the Telemetry section in file /opt/ufm/files/conf/gv.cfg 
    2. Inside /opt/ufm/files/conf/telemetry_defaults/launch_ibdiagnet_config.ini file, please replace plugin_env_PROMETHEUS_ENDPOINT=http://0.0.0.0:9001 with plugin_env_PROMETHEUS_ENDPOINT=http://0:0:0:0:0:0:0:0:9001

Usage
--------------------------------------------------------
### 1.Set the plugin configurations by the following API:

   METHOD: _POST_
   
   URL: _https://[HOST-IP]/ufmRest/plugin/tfs/conf_
   
   Payload Example:
   ```json
{
        "ufm-telemetry-endpoint": [{
            "host": "127.0.0.1",
            "url": "csv/metrics",
            "port": 9001,
            "interval": 30,
            "message_tag_name": "high_freq_endpoint"
        }],
        "fluentd-endpoint": {
            "host": "10.209.36.68",
            "port": 24226
        },
        "streaming": {
            "compressed_streaming": false,
            "bulk_streaming": true,
            "enabled": true,
            "stream_only_new_samples": true
        },
        "logs-config": {
            "log_file_backup_count": 5,
            "log_file_max_size": 10485760,
            "logs_file_name": "/log/tfs.log",
            "logs_level": "INFO"
        },
        "meta-fields":{
            "alias_node_description": "node_name",
            "alias_node_guid": "AID",
            "add_type":"csv"
        }
    }
   ```

   - Updating the configurations while the streaming is running requires restarting the plugin to load the new configurations

      
 Configuration Parameters Details:
--------------------------------------------------------

|                                    Parameter                                     | Required |                                                                                                                                   Description                                                                                                                                    |
|:--------------------------------------------------------------------------------:|:--------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|          [fluentd-endpoint.host](conf/fluentd_telemetry_plugin.cfg#L7)           |   True   |                                                                                                                  Hostname or IPv4 or IPv6 for Fluentd endpoint                                                                                                                   |
|          [fluentd-endpoint.port](conf/fluentd_telemetry_plugin.cfg#L8)           |   True   |                                                                               Port for Fluentd endpoint [this port should be the port which is configured in [fluentd.conf](conf/fluentd.conf#L4)]                                                                               |
|         [fluentd-endpoint.timeout](conf/fluentd_telemetry_plugin.cfg#L9)         |   True   |                                                                                                         Timeout for Fluentd endpoint streaming [Default is 120 seconds]                                                                                                          |
|       [ufm-telemetry-endpoint.host](conf/fluentd_telemetry_plugin.cfg#L2)        |   True   |                                                                                                  Hostname or IPv4 or IPv6 for The UFM Telemetry Endpoint [Default is 127.0.0.1]                                                                                                  |
|       [ufm-telemetry-endpoint.port](conf/fluentd_telemetry_plugin.cfg#L3)        |   True   |                                                                                                              Port for The UFM Telemetry Endpoint [Default is 9001]                                                                                                               |
|        [ufm-telemetry-endpoint.url](conf/fluentd_telemetry_plugin.cfg#L4)        |   True   |                                                                                    URL for The UFM Telemetry Endpoint [Default is 'csv/metrics', for Prometheus format you can use 'metrics']                                                                                    |
|     [ufm-telemetry-endpoint.interval](conf/fluentd_telemetry_plugin.cfg#L13)     |   True   |                                                                                                                    Streaming interval [Default is 30 seconds]                                                                                                                    |
| [ufm-telemetry-endpoint.message_tag_name](conf/fluentd_telemetry_plugin.cfg#L10) |  False   |                                                                              Message Tag Name for Fluentd endpoint message [Default is the ufm-telemetry-endpoint.host:ufm-telemetry-endpoint.port]                                                                              |
|        [streaming.bulk_streaming](conf/fluentd_telemetry_plugin.cfg#L14)         |   True   |                                                                 if True all telemetry records will be streamed in one message; otherwise, each record will be streamed in a separated message [Default is True]                                                                  |
|     [streaming.compressed_streaming](conf/fluentd_telemetry_plugin.cfg#L15)      |   True   | if True, the streamed data will be sent gzipped json and you have to make sure to configure the FluentD receiver with the right configurations (Check the FluentdD Deployment configurations section); otherwise, the message will be sent plain text as json [Default is False] |
|    [streaming.stream_only_new_samples](conf/fluentd_telemetry_plugin.cfg#L16)    |   True   |                                                                                                    If True, the plugin will stream only the changed values [Default is True]                                                                                                     |
|            [streaming.enabled](conf/fluentd_telemetry_plugin.cfg#L17)            |   True   |                                                                                     If True, the streaming will be started once the required configurations have been set [Default is False]                                                                                     |
|       [logs-config.logs_file_name](conf/fluentd_telemetry_plugin.cfg#L20)        |   True   |                                                                                                                     Log file name [Default = '/log/tfs.log']                                                                                                                     |
|         [logs-config.logs_level](conf/fluentd_telemetry_plugin.cfg#L22)          |   True   |                                                                                                                                Default is 'INFO'                                                                                                                                 |
|      [logs-config.max_log_file_size](conf/fluentd_telemetry_plugin.cfg#L24)      |   True   |                                                                                                                Maximum log file size in Bytes [Default is 10 MB]                                                                                                                 |
|    [logs-config.log_file_backup_count](conf/fluentd_telemetry_plugin.cfg#L26)    |   True   |                                                                                                                Maximum number of backup log files [Default is 5]                                                                                                                 |

   - Multiple UFM Telemetry endpoints:

You can configure the TFS plugin to poll the metrics from multiple endpoints, and to do so, you can add the telemetry endpoints configurations using the conf API.
Each added endpoint will have its own polling/streaming interval.

Payload example with multiple UFM Telemetry endpoints:

   ```json
{
        "ufm-telemetry-endpoint": [{
            "host": "127.0.0.1",
            "url": "csv/metrics",
            "port": 9001,
            "interval": 10,
            "message_tag_name": "high_freq_endpoint"
        },{
            "host": "127.0.0.1",
            "url": "csv/metrics",
            "port": 9002,
            "interval": 60,
            "message_tag_name": "low_freq_endpoint"
        }],
        "fluentd-endpoint": {
            "host": "10.209.36.68",
            "port": 24226
        }
    }
   ```

   - Sharding in UFM Telemetry :

The sharding functionality that is built into UFM telemetry, 
allows for efficient data polling from multiple telemetry metrics endpoints. 
This feature is particularly useful when dealing with large amounts of data or when operating in a network with limited bandwidth.

How To Use Sharding:

To use the sharding functionality, you need to add specific parameters to the URL of the configured telemetry endpoint.
These parameters include **num_shards**, **shard**, and **sharding_field**.

Here is an example of how to use these parameters with the TFS configurations payload:

   ```json
{
        "ufm-telemetry-endpoint": [{
            "host": "127.0.0.1",
            "url": "csv/xcset/ib_basic_debug?num_shards=3&shard=0&sharding_field=port_guid",
            "port": 9002,
            "interval": 120
        },{
            "host": "127.0.0.1",
            "url": "csv/xcset/ib_basic_debug?num_shards=3&shard=1&sharding_field=port_guid",
            "port": 9002,
            "interval": 120
        },{
            "host": "127.0.0.1",
            "url": "csv/xcset/ib_basic_debug?num_shards=3&shard=2&sharding_field=port_guid",
            "port": 9002,
            "interval": 120
        }],
        "fluentd-endpoint": {
            "host": "10.209.36.68",
            "port": 24226
        }
    }
   ```

In this example, the telemetry data is divided into three shards (`num_shards=3`), 
and each endpoint with a different shard (`shard=0`, `shard=1`, `shard=2`). 
The `sharding_field` parameter is used to specify the field on which the data is to be sharded.
In the provided example, `sharding_field` is set to `port_guid`. 
This means that the data is divided into shards based on the `port_guid` field. 
This field was chosen because it provides a convenient way to divide the data into distinct, non-overlapping shards.

Tuning the Sharding:

For optimal performance, it is recommended to tune the sharding so that a single shard transfers in about 10-15 seconds. This leaves plenty of overhead to avoid timeout issues. 
You may need to experiment with the number of shards to achieve this. For instance, if your network is slow, you might need to increase the number of shards.



   - Records ٌMeta-fields:
   
   Meta fields are user-defined additional fields of each streamed record with two types: Aliases and new constant fields.
        
  1) Aliases: add data of field "exact_name" to meta fields of record with new "alias_name".
      Aliases match only exact names and will apper in data record
                
    alias_exact_name=alias_name
    
  2) Constants: add new field "new_field_name" with constant data sting "constant_value"to the meta fields.
      Names should be unique.
      
    add_new_field_name=constant_value
  
  Example for meta-fields section inside the conf payload
  
```json
{
        "meta-fields":{
            "alias_node_description": "node_name",
            "alias_node_guid": "AID",
            "add_type":"csv"
        }
    }
```

The output record after adding these meta-fields will be:
```json
{
      "timestamp": "1644411135311315",
      "source_id": "0xe41d2d030003e450",
      "node_guid": "e41d2d030003e450",
      "port_guid": "e41d2d030003e450",
      "port_num": "10",
      "node_description": "SwitchIB Mellanox Technologies",
      "node_name": "SwitchIB Mellanox Technologies",
      "AID": "e41d2d030003e450",
      "type": "csv"
}
```


### 2.Get the plugin configurations by the following API:

   METHOD: _GET_
   
   URL: _https://[HOST-IP]/ufmRest/plugin/tfs/conf_

### 3. Get the streaming attributes configurations by the following API:

   METHOD: _GET_
   
   URL: _https://[HOST-IP]/ufmRest/plugin/tfs/conf/attributes_
   
   Response: JSON contains all the attributes and their configurations:
   
```json lines   
{ ...
  "ExcessiveBufferOverrunErrorsExtended": {
    "enabled": true,
    "name": "ExcessiveBufferOverrunErrorsExtended"
  },
  "LinkDownedCounterExtended": {
    "enabled": true,
    "name": "LinkDownedCounterExtended"
  },
  "LinkErrorRecoveryCounterExtended": {
    "enabled": true,
    "name": "LinkErrorRecoveryCounterExtended"
  },
  "LocalLinkIntegrityErrorsExtended": {
    "enabled": true,
    "name": "LocalLinkIntegrityErrorsExtended"
  }
  ...
}
```

### 4. Update the streaming attributes configurations by the following API:

   METHOD: _POST_
   
   URL: _https://[HOST-IP]/ufmRest/plugin/tfs/conf/attributes_
   
   Payload: JSON contains the attributes and their configurations:
   
```json lines   
{ ...
  "ExcessiveBufferOverrunErrorsExtended": {
    "enabled": true,
    "name": "ExcBuffOverrunErrExt"
  },
  "LinkDownedCounterExtended": {
    "enabled": false
  },
  "LinkErrorRecoveryCounterExtended": {
    "enabled": true,
    "name": "linkErrRecCountExt"
  },
  "LocalLinkIntegrityErrorsExtended": {
    "enabled": true,
    "name": "localLinkIntErrExt"
  }
  ...
}
```

|     Parameter     | Required |                         Description                          |
|:-----------------:|:--------:|:------------------------------------------------------------:|
| attribute.enabled |   True   | If True, the **attribute** will be part of the streamed data |
|  attribute.name   |   True   |   The name of the **attribute** in the streamed json data    |

*Updating the streaming attributes configurations will be reflected automatically and applied on the next streaming period. 

### 5. Get the streaming performance statistics by the following API:

   METHOD: _GET_
   
   URL: _https://[HOST-IP]/ufmRest/plugin/tfs/metrics
   
   Response: Text contains performance metrics for the last streaming interval in Prometheus format:
   
```text lines
# HELP num_of_processed_counters_in_last_msg Number of processed counters/attributes in the last streaming interval
# TYPE num_of_processed_counters_in_last_msg gauge
num_of_processed_counters_in_last_msg{endpoint="10.209.36.68:9001/csv/xcset/ib_basic_debug"} 176.0
num_of_processed_counters_in_last_msg{endpoint="10.209.36.67:9001/csv/xcset/ib_basic_debug"} 189.0
# HELP num_of_streamed_ports_in_last_msg Number of processed ports in the last streaming interval
# TYPE num_of_streamed_ports_in_last_msg gauge
num_of_streamed_ports_in_last_msg{endpoint="10.209.36.68:9001/csv/xcset/ib_basic_debug"} 6.0
num_of_streamed_ports_in_last_msg{endpoint="10.209.36.67:9001/csv/xcset/ib_basic_debug"} 4.0
# HELP streaming_time_seconds Time period for last streamed message in seconds
# TYPE streaming_time_seconds gauge
streaming_time_seconds{endpoint="10.209.36.68:9001/csv/xcset/ib_basic_debug"} 0.064626
streaming_time_seconds{endpoint="10.209.36.67:9001/csv/xcset/ib_basic_debug"} 0.025279
# HELP telemetry_expected_response_size_bytes Expected size of the last received telemetry response in bytes
# TYPE telemetry_expected_response_size_bytes gauge
telemetry_expected_response_size_bytes{endpoint="10.209.36.68:9001/csv/xcset/ib_basic_debug"} 5156.0
telemetry_expected_response_size_bytes{endpoint="10.209.36.67:9001/csv/xcset/ib_basic_debug"} 4726.0
# HELP telemetry_received_response_size_bytes Actual size of the last received telemetry response in bytes
# TYPE telemetry_received_response_size_bytes gauge
telemetry_received_response_size_bytes{endpoint="10.209.36.68:9001/csv/xcset/ib_basic_debug"} 5156.0
telemetry_received_response_size_bytes{endpoint="10.209.36.67:9001/csv/xcset/ib_basic_debug"} 4726.0
# HELP telemetry_response_time_seconds Response time of the last telemetry request in seconds
# TYPE telemetry_response_time_seconds gauge
telemetry_response_time_seconds{endpoint="10.209.36.68:9001/csv/xcset/ib_basic_debug"} 0.028893
telemetry_response_time_seconds{endpoint="10.209.36.67:9001/csv/xcset/ib_basic_debug"} 0.07777
# HELP telemetry_response_process_time_seconds Processing time of the last received telemetry response in seconds
# TYPE telemetry_response_process_time_seconds gauge
telemetry_response_process_time_seconds{endpoint="10.209.36.68:9001/csv/xcset/ib_basic_debug"} 0.00455
telemetry_response_process_time_seconds{endpoint="10.209.36.67:9001/csv/xcset/ib_basic_debug"} 0.003142

```

|                Attribute                |                            Description                             |
|:---------------------------------------:|:------------------------------------------------------------------:|
|    num_of_streamed_ports_in_last_msg    |        # of processed ports in the last streaming interval         |
|  num_of_processed_counters_in_last_msg  | # of processed counters/attributes in the last streaming interval  |
|         streaming_time_seconds          |          Time period for last streamed message in seconds          |
| telemetry_expected_response_size_bytes  |   Expected size of the last recivied telemetry response in bytes   |
| telemetry_received_response_size_bytes  |    Actual size of the last recivied telemetry response in bytes    |
|     telemetry_response_time_seconds     |       Response time of the last telemetry request in seconds       |
| telemetry_response_process_time_seconds | Processing time of the last recivied telemetry response in seconds |
