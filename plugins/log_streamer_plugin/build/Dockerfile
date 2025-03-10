FROM fluentd:v1.16.2-debian-1.1
USER root
LABEL maintainer="sfeld@nvidia.com"

ARG SRC_BASE_DIR=log_streamer_plugin

# Create the directory for the partial lists
RUN mkdir -p /var/lib/apt/lists/partial && \
mkdir -p /var/log/fluentd && \
chown -R fluent:fluent /var/log/fluentd

# Install build dependencies
RUN apt-get update && apt-get install -y \
supervisor \
build-essential \
ruby-dev \
netcat \
curl \
iputils-ping \
tcpdump \
iproute2 \
vim \
&& rm -rf /var/lib/apt/lists/*

# Install syslog plugin with specific version
RUN gem install fluent-plugin-remote_syslog

COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh ${SRC_BASE_DIR}/scripts/upgrade.sh /
COPY ${SRC_BASE_DIR}/src/log_streamer_entrypoint.sh /log_streamer_entrypoint.sh
COPY ${SRC_BASE_DIR}/conf/supervisord_log_streamer.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/build/config/log_streamer_conf.ini /log_streamer_conf.ini
COPY ${SRC_BASE_DIR}/src/update_log_streamer_conf.sh /update_log_streamer_conf.sh
COPY ${SRC_BASE_DIR}/src/create_fluent_conf.sh /create_fluent_conf.sh

# Make scripts executable
RUN chmod +x /init.sh /deinit.sh /upgrade.sh /log_streamer_entrypoint.sh /update_log_streamer_conf.sh /create_fluent_conf.sh

# Set default command
# Copy your configuration
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord_log_streamer.conf"]