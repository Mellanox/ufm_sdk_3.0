FROM ubuntu:18.04 AS ndt_base_ubuntu18

ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

LABEL maintainer="atolikin@nvidia.com"

RUN apt-get update && apt-get -y install supervisor python3 python3-pip

RUN python3 -m pip install flask flask_restful requests twisted apscheduler

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/

COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY config/init.sh /init.sh
COPY config/ufm_plugin_ndt_httpd.conf ${BASE_PATH}/ufm_plugin_ndt_httpd.conf
COPY config/ndt.conf ${BASE_PATH}/ndt.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
