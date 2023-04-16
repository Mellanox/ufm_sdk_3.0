FROM ubuntu:20.04

LABEL maintainer="anana@nvidia.com"

ARG PLUGIN_NAME
ARG DEBIAN_FRONTEND=noninteractive
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/

COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh /

RUN apt-get update && apt-get -y install supervisor python3-pip

RUN python3 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/src/requirements.txt


CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
