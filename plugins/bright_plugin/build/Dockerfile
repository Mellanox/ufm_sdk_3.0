FROM ubuntu:20.04 AS bright_base_ubuntu20

LABEL maintainer="nasraj@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_bright
ARG SRC_BASE_DIR=bright_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh /
COPY ${SRC_BASE_DIR}/conf/bright_httpd_proxy.conf ${SRC_BASE_DIR}/conf/bright_plugin.cfg ${BASE_PATH}/

RUN apt-get update && apt-get -y install supervisor python3 python3-pip vim rsyslog

RUN python3 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]