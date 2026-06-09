FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG PLUGIN_NAME=ports_snapshot
ARG BASE_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}

COPY conf/supervisord.conf /etc/supervisor/conf.d/ports_snapshot.conf
COPY . ${BASE_PATH}/${PLUGIN_NAME}_plugin/
COPY scripts/init.sh scripts/deinit.sh scripts/upgrade.sh /

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates python3 python3-pip supervisor \
    && python3 -m pip install --no-cache-dir -r ${BASE_PATH}/${PLUGIN_NAME}_plugin/src/requirements.txt \
    && chmod +x /init.sh /deinit.sh /upgrade.sh \
    && rm -rf /var/lib/apt/lists/*

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
