FROM ubuntu:20.04 AS sysinfo_base_ubuntu20

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/ufm_plugin_sysinfo

LABEL maintainer="egershon@nvidia.com"

RUN apt-get update && apt-get -y install supervisor python3 python3-pip rsyslog curl iputils-ping

RUN python3 -m pip install requests apscheduler validators asyncio aiohttp

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh /
COPY config/sysinfo_httpd_proxy.conf config/sysinfo.conf config/ufm_plugin_sysinfo_httpd.conf ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
