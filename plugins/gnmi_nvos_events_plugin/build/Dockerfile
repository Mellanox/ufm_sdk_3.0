FROM ubuntu:22.04 AS ubuntu22

ENV TZ=Europe
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/gnmi_events_plugin

LABEL maintainer="atolikin@nvidia.com"

RUN apt update && apt -y install supervisor python3 python3-pip mc
# removing to avoid vulnerabilities
RUN apt -y remove linux-libc-dev

RUN python3 -m pip install pygnmi requests flask flask_restful aiohttp

COPY gnmi_events_server/ ${BASE_PATH}/gnmi_events_server/

RUN mkdir /data
COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/upgrade.sh /
COPY config/gnmi_events.conf config/gnmi_events_shared_volumes.conf config/gnmi_events_httpd_proxy.conf ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]