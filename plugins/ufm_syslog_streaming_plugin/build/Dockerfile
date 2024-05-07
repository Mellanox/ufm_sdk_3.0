FROM ubuntu:22.04 AS efs_base_ubuntu22

LABEL maintainer="anana@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_efs
ARG SRC_BASE_DIR=ufm_syslog_streaming_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh /

RUN apt-get update && apt-get -y install supervisor python3 python3-pip vim rsyslog curl sudo systemctl

# remove an unused library that caused a high CVE vulnerability issue https://redmine.mellanox.com/issues/3621856
RUN apt-get remove -y linux-libc-dev

# install the fluent-bit
RUN curl https://raw.githubusercontent.com/fluent/fluent-bit/master/install.sh | sh
# add the symbolink
RUN ln -s /opt/fluent-bit/bin/fluent-bit /etc/init.d/fluent-bit

COPY ${SRC_BASE_DIR}/conf/parsers.conf /etc/fluent-bit/

RUN python3 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
