FROM ubuntu:20.04 AS tfs_base_ubuntu20

LABEL maintainer="anana@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_tfs
ARG SRC_BASE_DIR=ufm_telemetry_stream_to_fluentd

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh /
COPY ${SRC_BASE_DIR}/conf/tfs_httpd_proxy.conf ${SRC_BASE_DIR}/conf/ufm-telemetry-stream-to-fluentd.cfg ${SRC_BASE_DIR}/conf/fluentd.conf ${BASE_PATH}/

RUN apt-get update && apt-get -y install supervisor python3 python3-pip vim rsyslog

RUN python3 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]