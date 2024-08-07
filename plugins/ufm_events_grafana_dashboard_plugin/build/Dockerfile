# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

LABEL maintainer="anana@nvidia.com"

ARG PLUGIN_NAME
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin
ENV DEBIAN_FRONTEND=noninteractive

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY ${SRC_BASE_DIR}/scripts/ /


# Run installation scripts
RUN /install_fluentd.sh
RUN /install_loki.sh
RUN /install_grafana.sh

# Install Supervisor
RUN apt-get update && apt-get install -y supervisor vim tzdata

# move /etc/supervisor from the /etc, /etc dir will be overridden by the shared volume
RUN cp -r /etc/supervisor /

RUN sed -i 's|/etc/supervisor/conf.d/\*.conf|/supervisor/conf.d/\*.conf|g' /supervisor/supervisord.conf

# Copy Supervisor configuration file
COPY ${SRC_BASE_DIR}/conf/supervisord.conf /supervisor/conf.d/

# Start services using supervisord
CMD ["/usr/bin/supervisord", "-c", "/supervisor/supervisord.conf"]
