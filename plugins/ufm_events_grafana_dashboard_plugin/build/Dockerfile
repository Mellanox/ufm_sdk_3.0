FROM ubuntu:22.04

LABEL maintainer="anana@nvidia.com"

ARG PLUGIN_NAME
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}
ARG SRC_BASE_DIR=${PLUGIN_NAME}_plugin
ARG ETC_ALTERNATIVE_PATH=/var/etc
ARG SUPERVISOR_PATH=${ETC_ALTERNATIVE_PATH}/supervisor
ENV DEBIAN_FRONTEND=noninteractive
ENV REQUIRED_UFM_VERSION=6.12.0

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY ${SRC_BASE_DIR}/scripts/ /

RUN apt-get update && apt-get upgrade -y && \
    # Install plugin dependacies
    apt-get install -y supervisor vim tzdata wget unzip curl \
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
    wget https://github.com/grafana/loki/releases/download/v3.1.0/loki-linux-amd64.zip && \
    unzip loki-linux-amd64.zip && \
    mv loki-linux-amd64 /usr/local/bin/loki && \
    rm loki-linux-amd64.zip && \
    # Install Grafana
    wget https://dl.grafana.com/oss/release/grafana_11.1.0_amd64.deb && \
    dpkg -i grafana_11.1.0_amd64.deb && \
    rm grafana_11.1.0_amd64.deb && \
    # Final cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# move /etc/supervisor from the /etc, /etc dir will be overridden by the shared volume
RUN mkdir -p ${ETC_ALTERNATIVE_PATH} && mv /etc/supervisor ${ETC_ALTERNATIVE_PATH}

RUN sed -i "s|/etc/supervisor/conf.d/\*.conf|${SUPERVISOR_PATH}/conf.d/\*.conf|g" ${SUPERVISOR_PATH}/supervisord.conf

# Copy Supervisor configuration file
COPY ${SRC_BASE_DIR}/conf/supervisord.conf ${SUPERVISOR_PATH}/conf.d/

# Start services using supervisord
CMD ["/usr/bin/supervisord", "-c", "/var/etc/supervisor/supervisord.conf"]
