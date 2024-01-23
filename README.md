# UFM SDK 3.0



A new open-source SDK project for NVIDIA UFM ([Unified Fabric Manager](https://www.nvidia.com/en-us/networking/infiniband/ufm/))

![image](https://user-images.githubusercontent.com/3473601/166264210-740f11cd-e890-4e40-ad97-c95fafe32591.png)

## Main Features 

- **Scripts:**
  - list of python scripts as examples how to collect data and operate devices via UFM REST API

- **Plugins:**
  - [SLURM Integration Plugin](plugins/SLURM-Integration/README.md):Utilize UFM with SLURM to monitor network bandwidth, congestion, errors, and resource utilization of SLURM job compute nodes.
    
  - [UFM NDT Plugin](plugins/UFM_NDT_Plugin/README.md): Compare topologies, manage opensm input file creation, and merge topologies for enhanced UFM functionality.
  - [Advanced Hello World Plugin](plugins/advanced_hello_world_plugin/README.md): An advanced example demonstrating the construction of plugins for both backend and GUI.
  - [Bright Plugin](plugins/bright_plugin/README.md): Augment UFM's network perspective with data from Bright Cluster Manager, improving network-centered root cause analysis (RCA) tasks.
  - [Fluentd Telemetry Plugin](plugins/fluentd_telemetry_plugin/README.md): Extract UFM telemetry counters via Prometheus metrics and stream them using the Fluentd protocol to the telemetry console.
  - [Fluentd Topology Plugin](plugins/fluentd_topology_plugin/README.md): Extract topology via UFM API and stream it using the Fluentd protocol to the telemetry console.
  - [Grafana InfiniBand Telemetry Plugin](plugins/grafana_infiniband_telemetry_plugin/README.md): Provides a new UFM telemetry Prometheus endpoint with human-readable labels for monitoring using Grafana.
  - [Grafana Telemetry Plugin](plugins/grafana_telemetry_plugin/README.md): Grafana dashboard to monitor UFM telemetry metrics collected by Prometheus Server.
  - [gRPC Streamer Plugin](plugins/grpc_streamer_plugin/README.md): Provides gRPC streaming of UFM REST API for enhanced communication.
  - [Hello World Plugin](plugins/hello_world_plugin/README.md): Basic example of a backend plugin with minimal requirements.
  - [PDR Deterministic Plugin](plugins/pdr_deterministic_plugin/README.md): Handles UFM Packet Drop Rate (PDR) Deterministic Plugin for port isolation.
  - [SNMP Receiver Plugin](plugins/snmp_receiver_plugin/README.md): Listens to SNMP traps from managed switches in the fabric and redirects them as events to UFM.
  - [Sysinfo Plugin](plugins/sysinfo_plugin/README.md): Queries commands to switches using AIOHttps communication.
  - [UFM Syslog Streaming Plugin](plugins/ufm_syslog_streaming_plugin/README.md): Extracts UFM events from UFM syslog and streams them to a remote Fluentd destination, with an option to duplicate syslog messages to a remote syslog destination.
  - [Zabbix Telemetry Plugin](plugins/zabbix_telemetry_plugin/README.md): Explains how to stream UFM events to Zabbix for monitoring.

- **Utils:**
   - tools for general usage over UFM REST API. some of them already in use in the available 3rd party plugins







## Documentation

[UFM REST API Documentation](https://docs.nvidia.com/networking/display/UFMEnterpriseRESTAPILatest)

[UFM User Manual](https://docs.nvidia.com/networking/display/UFMEnterpriseUMLatest)

[UFM Release Notes](https://docs.nvidia.com/networking/display/UFMEnterpriseUMLatest/Release+Notes)



## Relase Job:
Please use the following in order to build:
http://hpc-master.lab.mtl.com:8080/job/UFM_PLUGINS_RELEASE/
    

# Adding Plugins to CI Pipeline

This project supports integration of custom plugins into the Continuous Integration (CI) pipeline. The process for integrating your plugin is simple and described below.

## Prerequisites

Your plugin should have a dedicated `.ci` directory that contains a `ci_matrix.yaml` file. This file is used by the CI pipeline to manage the build process for your plugin.

You can use the `ci_matrix.yaml` file found in the `hello_world_plugin` directory as a template.
https://github.com/Mellanox/ufm_sdk_3.0/blob/main/plugins/hello_world_plugin/.ci/ci_matrix.yaml


## CI Configuration Steps

To add your plugin to the CI pipeline, follow these steps:

1. Create a `.ci` directory in your plugin's root directory.

2. In the `.ci` directory, create a `ci_matrix.yaml` file. Use the `ci_matrix.yaml` file in the `hello_world_plugin` directory as a template.

3. The CI pipeline will detect changes in your plugin directory and trigger the CI process. It uses the `ci_matrix.yaml` file in your plugin's `.ci` directory to manage the CI process.

## Important Note

If your plugin directory does not contain a `.ci` directory, the CI process will fail.

## CI Trigger

The CI pipeline gets triggered based on changes made to the plugins. If changes occur in multiple plugins, the pipeline will not trigger the individual `.ci` directories but instead trigger a default empty CI.

