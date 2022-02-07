Grafana Infiniband Telemetry
--------------------------------------------------------


This is to explain how to Monitor Infiniband Telemetry using [Grafana](https://grafana.com/) and [prometheus](https://prometheus.io/) 

we use Prometheus server to pull data from UFM Telemetry (Prometheus endpoint) and present it on Grafana dashboard

Prerequisites
--------------------------------------------------------

To install Grafana on your machine, please follow the [installation guide](https://grafana.com/docs/grafana/latest/installation/) .

To install Prometheus server on your machine, please follow the [installation guide](https://prometheus.io/download/)

Configuration
--------------------------------------------------------
a) Edit prometheus.yml

    # metrics_path : 'labels/metrics'
    # targets: ["{UFM enterprise IP}:{Prometheus endpoint port, usually 9001}"]

b) Run Prometheus server

c) Add Prometheus server as data source for Grafana

d) Import Infiniband_Telemetry.json to your Grafana dashboard

Use Grafana
--------------------------------------------------------
Monitor your network from Grafana dashboard!
![result](sample.png)


