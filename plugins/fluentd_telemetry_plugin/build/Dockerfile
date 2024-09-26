FROM ubuntu:22.04 AS tfs_base_ubuntu22

LABEL maintainer="anana@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_tfs
ARG TELEMETRY_BASE_PATH=/opt/ufm/telemetry
ARG SRC_BASE_DIR=fluentd_telemetry_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/
COPY ufm_sdk_tools/ ${BASE_PATH}/ufm_sdk_tools/

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh /
COPY ${SRC_BASE_DIR}/conf/tfs_httpd_proxy.conf ${SRC_BASE_DIR}/conf/fluentd_telemetry_plugin.cfg ${SRC_BASE_DIR}/conf/fluentd.conf ${BASE_PATH}/

COPY ${SRC_BASE_DIR}/lib/libfluent-bit.so ${SRC_BASE_DIR}/lib/libraw_msgpack_api.so  ${TELEMETRY_BASE_PATH}/collectx/lib/

RUN apt-get update && apt-get -y install supervisor python3 python3-pip vim rsyslog wget

# remove an unused library that caused a high CVE vulnerability issue https://redmine.mellanox.com/issues/3621861
RUN apt-get remove -y linux-libc-dev

RUN python3 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]