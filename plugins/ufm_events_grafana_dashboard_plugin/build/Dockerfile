FROM ubuntu:22.04

LABEL maintainer="anana@nvidia.com"

ARG PLUGIN_NAME
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin
ARG ETC_ALTERNATIVE_PATH=/var/etc
ARG SUPERVISOR_PATH=${ETC_ALTERNATIVE_PATH}/supervisor
ARG LOKI_VERSION=3.1.0
ARG PROMETHEUS_VERSION=2.54.0
ARG GRAFANA_VERSION=11.1.0
ENV DEBIAN_FRONTEND=noninteractive
ENV REQUIRED_UFM_VERSION=6.12.0

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/
COPY ${SRC_BASE_DIR}/scripts/ /

RUN apt-get update && apt-get upgrade -y && \
    # Install plugin dependacies
    apt-get install -y supervisor vim tzdata wget unzip curl python3 python3-pip \
    # Install Fluentd prerequisites
    gnupg build-essential ruby ruby-dev \
    # Install Grafana prerequisites
    libfontconfig1 musl || apt --fix-broken install -y && \
    # Install Fluentd
    gem install fluentd --no-document && \
    fluent-gem install fluent-plugin-script fluent-plugin-grafana-loki && \
    # Clean up Fluentd development packages
    apt-get remove --purge -y ruby-dev build-essential && \
    apt-get autoremove -y && \
    # Install Loki
    wget https://github.com/grafana/loki/releases/download/v"${LOKI_VERSION}"/loki-linux-amd64.zip && \
    unzip loki-linux-amd64.zip && \
    mv loki-linux-amd64 /usr/local/bin/loki && \
    rm loki-linux-amd64.zip && \
    # Install Prometheus
    wget https://github.com/prometheus/prometheus/releases/download/v"${PROMETHEUS_VERSION}"/prometheus-"${PROMETHEUS_VERSION}".linux-amd64.tar.gz && \
    tar -xvf prometheus-"${PROMETHEUS_VERSION}".linux-amd64.tar.gz && \
    mv prometheus-"${PROMETHEUS_VERSION}".linux-amd64/prometheus /usr/local/bin/prometheus && \
    rm -rf prometheus-"${PROMETHEUS_VERSION}".linux-amd64.tar.gz && \
    # Install Grafana
    wget https://dl.grafana.com/oss/release/grafana_"${GRAFANA_VERSION}"_amd64.deb && \
    dpkg -i grafana_"${GRAFANA_VERSION}"_amd64.deb && \
    rm grafana_"${GRAFANA_VERSION}"_amd64.deb && \
    # Final cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install the python packages
RUN python3 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/src/${PLUGIN_NAME}/requirements.txt

# move /etc/supervisor from the /etc, /etc dir will be overridden by the shared volume
RUN mkdir -p ${ETC_ALTERNATIVE_PATH} && \
    mv /etc/supervisor ${ETC_ALTERNATIVE_PATH} && \
    sed -i "s|/etc/supervisor/conf.d/\*.conf|${SUPERVISOR_PATH}/conf.d/\*.conf|g" ${SUPERVISOR_PATH}/supervisord.conf

# Copy Supervisor configuration file
COPY ${SRC_BASE_DIR}/conf/supervisord.conf ${SUPERVISOR_PATH}/conf.d/

CMD ["/bin/bash", "-c", "/entrypoint.sh"]
