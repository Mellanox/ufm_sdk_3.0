FROM mellanox/ufm-enterprise:latest

LABEL maintainer="atabachnik@nvidia.com"

ARG PLUGIN_NAME="ufm_consumer"
ARG DEBIAN_FRONTEND=noninteractive
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin
ARG LOG_LINK=/log
ARG LOG_DIR=/opt/ufm/files/log

SHELL ["/bin/bash", "-c"]

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/conf/ufm_consumer_plugin.conf /
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh ${SRC_BASE_DIR}/scripts/start_ufm.sh /

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    supervisor && \
    rm -rf /var/lib/apt/lists/* && \
    export MULTISUBNET_CONSUMER=true && \
    mkdir -p /dev/consumer_log && \
    chmod -R a+rw /dev/consumer_log && \
    unlink /opt/ufm/files  && \
    mv /opt/ufm/ufm_config_files /opt/ufm/files && \
    rm -rf ${LOG_DIR} && \
    ln -s ${LOG_LINK} ${LOG_DIR}
    

COPY ${SRC_BASE_DIR}/scripts/config_consumer.sh config_consumer.sh
COPY ${SRC_BASE_DIR}/conf/ufm_consumer_plugin.conf ufm_consumer_plugin.conf
ENTRYPOINT []
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

