FROM ubuntu:22.04 AS grafana-dashboard_base_ubuntu20

LABEL maintainer="anana@nvidia.com"

ARG DEBIAN_FRONTEND=noninteractive
ARG BASE_PATH=/opt/ufm/ufm_plugin_grafana-dashboard
ARG SRC_BASE_DIR=grafana_infiniband_telemetry_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh /

RUN apt-get update && apt-get -y install supervisor python3 python3-pip vim curl sudo systemctl apache2

#RUN apt-get update && apt-get upgrade -y linux-libc-dev
RUN apt-get remove -y linux-libc-dev

RUN python3 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
