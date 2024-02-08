FROM ubuntu:22.04 AS ubuntu22

ENV TZ=Europe
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/snmp_plugin

LABEL maintainer="atolikin@nvidia.com"

RUN apt update && apt -y install supervisor python3 python3-pip mc
# removing to avoid vulnerabilities
RUN apt -y remove linux-libc-dev

RUN python3 -m pip install pyasn1==0.4.8 pysnmp requests flask flask_restful aiohttp

COPY mibs/ ${BASE_PATH}/mibs/
COPY snmp_server/ ${BASE_PATH}/snmp_server/

RUN mkdir /data
COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh /
COPY config/snmp.conf config/snmp_shared_volumes.conf config/snmp_httpd_proxy.conf ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]