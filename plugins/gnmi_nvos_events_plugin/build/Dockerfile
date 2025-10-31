FROM ubuntu:24.04 AS ubuntu24

ENV TZ=Europe
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/gnmi_nvos_events_plugin

LABEL maintainer="atolikin@nvidia.com"

RUN apt update && apt -y install supervisor python3 python3-pip mc
# removing to avoid vulnerabilities
RUN apt -y remove linux-libc-dev
# update libtiff6 to fix CVE-2025-9900
RUN apt -y install --only-upgrade libtiff6

RUN python3 -m pip config set global.break-system-packages true
RUN python3 -m pip install pygnmi requests flask flask_restful aiohttp pycryptodome

COPY gnmi_events_server/ ${BASE_PATH}/gnmi_events_server/

RUN mkdir /data
COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/upgrade.sh /
COPY config/gnmi_nvos_events.conf config/gnmi_nvos_events_httpd_proxy.conf ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]