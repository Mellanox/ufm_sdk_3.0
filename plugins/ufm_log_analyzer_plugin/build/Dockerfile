FROM ubuntu:22.04


ARG PLUGIN_NAME
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY ${SRC_BASE_DIR}/scripts/ /

RUN apt update && apt install -y python3.10

# ENTRYPOINT [ "executable" ]
