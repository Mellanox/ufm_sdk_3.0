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

    
    > /opt/ufm/scripts/manage_ufm_plugins.py add -p tfs
  
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

Usage
--------------------------------------------------------
### 1.Set the plugin configurations by the following API:

   METHOD: _POST_
   
   URL: _https://[HOST-IP]/plugin/tfs/conf_
   
   Payload Example:
   ```json
{
    "fluentd-endpoint": {
        "host": "10.209.36.68",
        "message_tag_name": "",
        "port": "24226",
        "timeout": "120"
    },
    "streaming": {
        "interval": "10"
    },
    "ufm-telemetry-endpoint": {
        "host": "10.209.36.68",
        "port": "9001",
        "url": "enterprise"
    }
}
   ```

   - For the configuration parameters details:
      
 Running syntax
--------------------------------------------------------

| Parameter | Required | Description |
| :---: | :---: |:---: |
| [fluentd-endpoint.host](conf/ufm-telemetry-stream-to-fluentd.cfg#L7) | True |  Hostname or IP for Fluentd endpoint
| [fluentd-endpoint.port](conf/ufm-telemetry-stream-to-fluentd.cfg#L8) | True | Port for Fluentd endpoint [this port should be the port which is configured in [fluentd.conf](conf/fluentd.conf#L4)]
| [fluentd-endpoint.timeout](conf/ufm-telemetry-stream-to-fluentd.cfg#L9) | True | Timeout for Fluentd endpoint streaming [Default is 120 seconds]
| [fluentd-endpoint.message_tag_name](conf/ufm-telemetry-stream-to-fluentd.cfg#L10) | False | Message Tag Name for Fluentd endpoint message [Default is the ufm_telemetry_host]
| [ufm-telemetry-endpoint.host](conf/ufm-telemetry-stream-to-fluentd.cfg#L2) | True | Hostname or IP for The UFM Telemetry Endpoint
| [ufm-telemetry-endpoint.port](conf/ufm-telemetry-stream-to-fluentd.cfg#L3) | True | Port for The UFM Telemetry Endpoint [Default is 9001]
| [ufm-telemetry-endpoint.url](conf/ufm-telemetry-stream-to-fluentd.cfg#L4) | True | URL for The UFM Telemetry Endpoint [Default is 'enterprise']
| [streaming.interval](conf/ufm-telemetry-stream-to-fluentd.cfg#L14) | True | Streaming interval [Default is 10 seconds]


### 2.Get the plugin configurations by the following API:

   METHOD: _GET_
   
   URL: _https://[HOST-IP]/plugin/tfs/conf_



### 3.Start the streaming by the following API:

   METHOD: _POST_
   
   URL: _https://[HOST-IP]/plugin/tfs/start_


### 4.Stop the streaming by the following API:

   METHOD: _POST_
   
   URL: _https://[HOST-IP]/plugin/tfs/stop_

### 5.Check the the streaming status by the following API:

   METHOD: _POST_
   
   URL: _https://[HOST-IP]/plugin/tfs/status_
   
   Response: _0_ | _1_ [0=>Stopped | 1=>Running]
