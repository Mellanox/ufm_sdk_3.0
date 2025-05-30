FROM ubuntu:20.04 AS pdr_base_ubuntu20

ENV TZ=Israel
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

LABEL maintainer="drorl@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_pdr_deterministic
ARG CONF_PATH=${BASE_PATH}/conf
ARG SCRIPTS_PATH=${BASE_PATH}/scripts

EXPOSE 8000
EXPOSE 443
EXPOSE 9002

RUN apt-get update && apt-get -y install supervisor python3 python3-pip rsyslog vim curl sudo

RUN python3 -m pip install requests jsonschema pandas numpy aiohttp

# remove an unused library that caused a high CVE vulnerability issue https://redmine.mellanox.com/issues/3837452
RUN apt-get remove -y linux-libc-dev

# At this point 'utils' should be already copied into 'ufm_sim_web_service' directory
COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh /
COPY config/pdr_deterministic.conf ${CONF_PATH}/
COPY config/pdr_deterministic_httpd_proxy.conf ${CONF_PATH}/
COPY config/pdr_deterministic_shared_volumes.conf ${CONF_PATH}/
COPY scripts/init_pdr_conf.sh ${SCRIPTS_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
