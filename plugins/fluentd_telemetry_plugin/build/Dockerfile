# Builder - Install Python dependencies
FROM ubuntu:22.04 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python requirements
ARG SRC_BASE_DIR=fluentd_telemetry_plugin
COPY ${SRC_BASE_DIR}/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Runtime - Minimal production image
FROM ubuntu:22.04 AS tfs_base_ubuntu22

LABEL maintainer="anana@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_tfs
ARG TELEMETRY_BASE_PATH=/opt/ufm/telemetry
ARG SRC_BASE_DIR=fluentd_telemetry_plugin

# Optional: Enable dev tools for debugging (default: disabled)
ARG DEV_TOOLS=0

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    python3 \
    $(if [ "$DEV_TOOLS" = "1" ]; then echo "vim"; fi) \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Remove unused library that caused a high CVE vulnerability issue
# https://redmine.mellanox.com/issues/3621861
RUN apt-get remove -y linux-libc-dev 2>/dev/null || true

# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application code
COPY ${SRC_BASE_DIR}/src/ ${BASE_PATH}/${SRC_BASE_DIR}/src/
COPY ${SRC_BASE_DIR}/conf/ ${BASE_PATH}/${SRC_BASE_DIR}/conf/
COPY ${SRC_BASE_DIR}/scripts/ ${BASE_PATH}/${SRC_BASE_DIR}/scripts/
COPY ${SRC_BASE_DIR}/__init__.py ${BASE_PATH}/${SRC_BASE_DIR}/

# Only copy required modules
COPY utils/__init__.py ${BASE_PATH}/utils/
COPY utils/flask_server/ ${BASE_PATH}/utils/flask_server/
COPY utils/logger.py ${BASE_PATH}/utils/
COPY utils/utils.py ${BASE_PATH}/utils/
COPY utils/config_parser.py ${BASE_PATH}/utils/
COPY utils/json_schema_validator.py ${BASE_PATH}/utils/
COPY utils/args_parser.py ${BASE_PATH}/utils/
COPY utils/exception_handler.py ${BASE_PATH}/utils/
COPY utils/ufm_rest_client.py ${BASE_PATH}/utils/
COPY utils/fluentd/fluent/ ${BASE_PATH}/utils/fluentd/fluent/

# Only copy required SDK tools
COPY ufm_sdk_tools/__init__.py ${BASE_PATH}/ufm_sdk_tools/
COPY ufm_sdk_tools/src/__init__.py ${BASE_PATH}/ufm_sdk_tools/src/
COPY ufm_sdk_tools/src/utils/ ${BASE_PATH}/ufm_sdk_tools/src/utils/
COPY ufm_sdk_tools/src/xdr_utils/ ${BASE_PATH}/ufm_sdk_tools/src/xdr_utils/
COPY ufm_sdk_tools/src/config_parser_utils/ ${BASE_PATH}/ufm_sdk_tools/src/config_parser_utils/

# Copy configuration files
COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh ${SRC_BASE_DIR}/scripts/upgrade.sh /
COPY ${SRC_BASE_DIR}/conf/tfs_httpd_proxy.conf ${SRC_BASE_DIR}/conf/fluentd_telemetry_plugin.cfg ${SRC_BASE_DIR}/conf/fluentd.conf ${BASE_PATH}/

# Copy native libraries
COPY ${SRC_BASE_DIR}/lib/libfluent-bit.so ${TELEMETRY_BASE_PATH}/collectx/lib/
COPY ${SRC_BASE_DIR}/lib/libraw_msgpack_api.so ${TELEMETRY_BASE_PATH}/collectx/lib/

# Create necessary directories
RUN mkdir -p /log /config

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
