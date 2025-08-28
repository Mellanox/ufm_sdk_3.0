FROM ubuntu:24.04 AS ubuntu24

ENV TZ=Europe
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/snmp_plugin

LABEL maintainer="atolikin@nvidia.com"

RUN apt update && apt -y install software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update && apt -y install supervisor python3.10 python3.10-venv mc
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
RUN python3.10 -m ensurepip --upgrade
RUN python3.10 -m pip install --upgrade pip
RUN python3.10 -m pip install --upgrade setuptools==78.1.1
RUN ln -sf /usr/bin/python3.10 /usr/bin/python3
RUN ln -sf $(which pip3.10) /usr/bin/pip3

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3.10 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# removing to avoid vulnerabilities
RUN apt -y remove linux-libc-dev

# Upgrade setuptools in virtual environment to fix security vulnerabilities
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools==78.1.1

RUN python3 -m pip install pyasn1==0.4.8 pysnmp==4.4.12 requests flask flask_restful aiohttp

COPY mibs/ ${BASE_PATH}/mibs/
COPY snmp_server/ ${BASE_PATH}/snmp_server/

RUN mkdir /data
COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/upgrade.sh /
COPY config/snmp.conf config/snmp_shared_volumes.conf config/snmp_httpd_proxy.conf ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]