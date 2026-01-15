ARG ARCH
FROM nbu-harbor.gtm.nvidia.com/ufm/ufm_docker/ubuntu_base_${ARCH}_24_04:20260114 AS ndt_base_ubuntu24

ARG ARCH
ARG MOFED_VER=25.07-0.9.7.0
ARG MOFED_DIR=MLNX_OFED_LINUX-${MOFED_VER}-ubuntu24.04-${ARCH}

ENV TZ=Europe/Moscow
ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
LABEL maintainer="atolikin@nvidia.com"

RUN apt-get update && apt upgrade -y && apt-get -y install supervisor python3 python3-pip rsyslog mc wget cron logrotate vim libcap2 curl sudo libtiff6

RUN python3 -m pip install flask flask_restful requests pandas twisted apscheduler pyDes "tzlocal<3.0" --break-system-packages

# Install OFED
RUN wget -q -r -np -nH --cut-dirs=5 http://nbu-nfs.mellanox.com/auto/mswg/release/MLNX_OFED/MLNX_OFED_LINUX-${MOFED_VER}/${MOFED_DIR}/ && \
    cd  ${MOFED_DIR} && \
    chmod +x mlnxofedinstall *.sh && \
    ./mlnxofedinstall --without-fw-update --user-space-only --skip-distro-check --skip-unsupported-devices-check --force && \
    cd ../ && \
    rm -rf ${MOFED_DIR}

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/
COPY ufm_sdk_tools/ ${BASE_PATH}/ufm_sdk_tools/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/ui_build.sh config/upgrade.sh /
COPY config/ndt_logrotate.conf /etc/logrotate.d/ndt
COPY config/ndt_httpd_proxy.conf config/ndt.conf config/ufm_plugin_ndt_httpd.conf config/ndt_ui_conf.json ${BASE_PATH}/

RUN /ui_build.sh

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
