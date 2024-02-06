FROM ubuntu:20.04

LABEL maintainer="atabachnik@nvidia.com"

ARG PLUGIN_NAME="ufm_consumer"
ARG DEBIAN_FRONTEND=noninteractive
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/conf/ufm_consumer_plugin.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh ${SRC_BASE_DIR}/scripts/start_ufm.sh /


RUN apt-get update && apt-get -y install supervisor python3.9 python3-pip vim curl sudo openssh-client bc acl iproute2 sshpass lftp zip rsync telnet qperf sqlite3 apache2 ssl-cert snmpd cron logrotate chrpath gawk libcairo2

# Install UFM somehow
RUN sshpass -v -p 3tango  scp -o StrictHostKeyChecking=no -r root@r-ufm55:/mswg/release/ufm/ufm-enterprise/6.16.0/6.16.0-3/ufm-6.16.0-3.ubuntu20.x86_64.mofed5.tgz . && \
        tar xvzf ./ufm-6.16.0-3.ubuntu20.x86_64.mofed5.tgz -C /tmp && \
        cd /tmp/ufm-6.16.0-3.ubuntu20.x86_64.mofed5/ && \
        export MULTISUBNET_CONSUMER=true && \
        echo -e '#!/bin/bash\nexit 0' > check_ports.sh && \
        ./install.sh -q && \
        mkdir -p /dev/consumer_log && \
        chmod -R a+rw /dev/consumer_log && \
        cd - && \
        rm -rf /tmp/ufm-6.16.0-3.ubuntu20.x86_64.mofed5 && \ 
        rm -f ufm-6.16.0-3.ubuntu20.x86_64.mofed5.tgz

COPY ${SRC_BASE_DIR}/scripts/config_consumer.sh config_consumer.sh
COPY ${SRC_BASE_DIR}/conf/ufm_consumer_plugin.conf ufm_consumer_plugin.conf
RUN ${BASE_PATH}/${SRC_BASE_DIR}/scripts/ui_build.sh ${PLUGIN_NAME}
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

