FROM ubuntu:20.04 AS ubuntu20

ENV TZ=Europe
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/snmp_plugin

LABEL maintainer="atolikin@nvidia.com"

RUN apt update && apt -y install supervisor python3 python3-pip mc

RUN python3 -m pip install pysnmp requests flask flask_restful aiohttp

COPY mibs/ ${BASE_PATH}/mibs/
COPY snmp_server/ ${BASE_PATH}/snmp_server/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh /
COPY config/snmp.conf config/snmp_shared_volumes.conf config/snmp_httpd_proxy.conf ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]