FROM ubuntu:18.04 AS ndt_base_ubuntu18

ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

LABEL maintainer="atolikin@nvidia.com"

RUN apt-get update && apt-get -y install supervisor python3 python3-pip rsyslog mc

RUN python3 -m pip install flask flask_restful requests twisted apscheduler "tzlocal<3.0"

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh /
COPY config/ndt_httpd_proxy.conf  config/ndt.conf ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
