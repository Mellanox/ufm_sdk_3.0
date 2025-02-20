Grafana Infiniband Telemetry
--------------------------------------------------------


This is to explain how to Monitor Infiniband Telemetry using [Grafana](https://grafana.com/) and [prometheus](https://prometheus.io/) 

we use Prometheus server to pull data from UFM Telemetry (Prometheus endpoint) and present it on Grafana dashboard

Overview
--------------------------------------------------------

NVIDIA UFM Telemetry platform provides network validation tools to monitor network performance and conditions, capturing and streaming rich real-time network telemetry information, application workload usage to an on-premise or cloud-based database for further analysis. As a fabric manager, the UFM Telemetry holds a real-time network telemetry information of the network topology. This information should be monitored, over time (as it can change with time) towards a monitoring system like Grafana. In order to do so, we present UFM Telemetry Grafana Plugin.


Prerequisites
--------------------------------------------------------

To install Grafana on your machine, please follow the [installation guide](https://grafana.com/docs/grafana/latest/installation/) .

To install Prometheus server on your machine, please follow the [installation guide](https://prometheus.io/download/)

Configuration
--------------------------------------------------------
a) Configure Prometheus endpoint with [Prometheus Label Generation](https://docs.nvidia.com/networking/display/UFMTelemetryLatest/Prometheus+Endpoint+Support#PrometheusEndpointSupport-PrometheusLabelGenerationPrometheusLabelGeneration)

b) Edit prometheus.yml in Prometheus Server

    # metrics_path : 'labels/enterprise'
    # targets: ["{UFM enterprise IP}:{Prometheus endpoint port, usually 9001}"]

c) Run Prometheus server

d) Add Prometheus server as data source for Grafana and name it prometheus (case-sensitive)

e) Import Infiniband_Telemetry.json to your Grafana dashboard

Use Grafana
--------------------------------------------------------
Monitor your network from Grafana dashboard!
![result](sample.png)


