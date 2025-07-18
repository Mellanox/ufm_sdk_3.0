FROM harbor.mellanox.com/ufm/ufm_docker/ubuntu_base_24_04:20250513 AS ndt_base_ubuntu24

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

LABEL maintainer="atolikin@nvidia.com"

RUN apt-get update && apt upgrade -y && apt-get -y install supervisor python3 python3-pip rsyslog mc wget cron logrotate vim libcap2 curl sudo

RUN python3 -m pip install flask flask_restful requests pandas twisted apscheduler pyDes "tzlocal<3.0" --break-system-packages

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/
COPY ufm_sdk_tools/ ${BASE_PATH}/ufm_sdk_tools/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/ui_build.sh config/upgrade.sh /
COPY config/ndt_logrotate.conf /etc/logrotate.d/ndt
COPY config/ndt_httpd_proxy.conf config/ndt.conf config/ufm_plugin_ndt_httpd.conf config/ndt_ui_conf.json ${BASE_PATH}/

RUN /ui_build.sh

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
