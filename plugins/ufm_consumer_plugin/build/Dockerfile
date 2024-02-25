FROM ubuntu:20.04

LABEL maintainer="atabachnik@nvidia.com"

ARG PLUGIN_NAME="ufm_consumer"
ARG UFM_TAR_PREFIX="ufm"
ARG UFM_TAR_SUFIX="ubuntu20.x86_64.mofed5"
ARG DEBIAN_FRONTEND=noninteractive
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/
COPY ${UFM_DISTRO_PREFIX}*${UFM_TAR_SUFIX}.tgz /tmp
COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/conf/ufm_consumer_plugin.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh ${SRC_BASE_DIR}/scripts/start_ufm.sh /


RUN apt-get update && apt-get -y install supervisor python3-pip vim curl sudo openssh-client bc acl iproute2 sshpass lftp zip rsync telnet qperf sqlite3 apache2 ssl-cert snmpd cron logrotate chrpath gawk libcairo2

# Install UFM
RUN     tar xvzf /tmp/${UFM_DISTRO_PREFIX}*${UFM_TAR_SUFIX}.tgz -C /tmp && \
        cd /tmp/${UFM_DISTRO_PREFIX}*${UFM_TAR_SUFIX}/ && \
        export MULTISUBNET_CONSUMER=true && \
        echo -e '#!/bin/bash\nexit 0' > check_ports.sh && \
        ./install.sh -q && \
        mkdir -p /dev/consumer_log && \
        chmod -R a+rw /dev/consumer_log && \
        cd - && \
        rm -rf /tmp/${UFM_DISTRO_PREFIX}*${UFM_TAR_SUFIX} && \
        rm -f /tmp/${UFM_DISTRO_PREFIX}*${UFM_TAR_SUFIX}.tgz

COPY ${SRC_BASE_DIR}/scripts/config_consumer.sh config_consumer.sh
COPY ${SRC_BASE_DIR}/conf/ufm_consumer_plugin.conf ufm_consumer_plugin.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

