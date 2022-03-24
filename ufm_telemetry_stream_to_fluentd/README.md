UFM Telemetry endpoint stream To Fluentd endpoint (TFS)
--------------------------------------------------------


This plugin is used to extract UFM telemetry counters via [Prometheus](https://prometheus.io/) metrics and stream it via [fluentd](https://www.fluentd.org/) protocol to telemetry console

Overview
--------------------------------------------------------

NVIDIA UFM Telemetry platform provides network validation tools to monitor network performance and conditions, capturing and streaming rich real-time network telemetry information, application workload usage to an on-premise or cloud-based database for further analysis.
As a fabric manager, the UFM Telemetry holds a real-time network telemetry information of the network topology. This information should be reflected, over time (as it can change with time) towards telemetry console. In order to do so, we present stream the UFM Telemetry data To the [Fluentd](https://www.fluentd.org/) plugin



Plugin Deployment
--------------------------------------------------------

To deploy the plugin on UFM Appliance:

- Login as admin;
- Run 


    > enable;
    > config terminal;

- make sure that UFM is running with :


    > show ufm status;
- If UFM is down then run it with 


    > ufm start;
- Make sure that TFS plugin is not added yet by running 


    > show ufm plugin;
- Pull the latest plugin container
  - In case of HA pull the plugin on the standby node as well;
- To enable & start the plugin, run: 


    > ufm plugin tfs add;

- Check that plugin is up and running with
    
    
    > ufm plugin show;


To deploy the plugin with UFM Enterprise (SA or HA):
- Install the latest version of UFM.
- Run UFM by running:


    > /etc/init.d/ufmd start
 
- Pull the latest plugin container
  - In case of HA pull the plugin on the standby node as well;
- To enable & start the plugin, run :

    
    > /opt/ufm/scripts/manage_ufm_plugins.sh add -p tfs
  
- Check that plugin is up and running with
 
 
    >docker ps;

Log file tfs.log is located in /opt/ufm/files/log on the host.

FluentdD Deployment configurations
--------------------------------------------------------

- Pull the [Fluentd Docker](https://hub.docker.com/r/fluent/fluentd/) by running:
 
 
    > docker pull fluent/fluentd
    
- Run the Fluentd docker by running:

    
    > docker run -ti --rm --network host -v /tmp/fluentd:/fluentd/etc fluentd -c /fluentd/etc/fluentd.conf -v

* We provide [fluentd.conf](conf/fluentd.conf) as a fluentd configurations sample.
* For IPv6, please replace [fluentd host address](conf/fluentd.conf#3) (bind 0.0.0.0) with (bind ::)

Usage
--------------------------------------------------------
### 1.Set the plugin configurations by the following API:

   METHOD: _POST_
   
   URL: _https://[HOST-IP]/ufmRest/plugin/tfs/conf_
   
   Payload Example:
   ```json
{
        "ufm-telemetry-endpoint": {
            "host": "127.0.0.1",
            "url": "labels/csv/metrics",
            "port": 9001
        },
        "fluentd-endpoint": {
            "host": "10.209.36.68",
            "port": "24226"
        },
        "streaming": {
            "interval": 10,
            "bulk_streaming": true,
            "enabled": true
        },
        "meta-fields":{
            "alias_node_description": "node_name",
            "alias_node_guid": "AID",
            "add_type":"csv"
        }
    }
   ```
      
 Configuration Parameters Details:
--------------------------------------------------------

| Parameter | Required | Description |
| :---: | :---: |:---: |
| [fluentd-endpoint.host](conf/ufm-telemetry-stream-to-fluentd.cfg#L7) | True |  Hostname or IPv4 or IPv6 for Fluentd endpoint
| [fluentd-endpoint.port](conf/ufm-telemetry-stream-to-fluentd.cfg#L8) | True | Port for Fluentd endpoint [this port should be the port which is configured in [fluentd.conf](conf/fluentd.conf#L4)]
| [fluentd-endpoint.timeout](conf/ufm-telemetry-stream-to-fluentd.cfg#L9) | True | Timeout for Fluentd endpoint streaming [Default is 120 seconds]
| [fluentd-endpoint.message_tag_name](conf/ufm-telemetry-stream-to-fluentd.cfg#L10) | False | Message Tag Name for Fluentd endpoint message [Default is the ufm_telemetry_host]
| [ufm-telemetry-endpoint.host](conf/ufm-telemetry-stream-to-fluentd.cfg#L2) | True | Hostname or IPv4 or IPv6 for The UFM Telemetry Endpoint [Default is 127.0.0.1]
| [ufm-telemetry-endpoint.port](conf/ufm-telemetry-stream-to-fluentd.cfg#L3) | True | Port for The UFM Telemetry Endpoint [Default is 9001]
| [ufm-telemetry-endpoint.url](conf/ufm-telemetry-stream-to-fluentd.cfg#L4) | True | URL for The UFM Telemetry Endpoint [Default is 'labels/csv/metrics']
| [streaming.interval](conf/ufm-telemetry-stream-to-fluentd.cfg#L13) | True | Streaming interval [Default is 10 seconds]
| [streaming.bulk_streaming](conf/ufm-telemetry-stream-to-fluentd.cfg#L14) | True | if True all telemetry records will be streamed in one message; otherwise, each record will be streamed in a separated message [Default is True]
| [streaming.enabled](conf/ufm-telemetry-stream-to-fluentd.cfg#L15) | True | If True, the streaming will be started once the required configurations have been set [Default is False]


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

