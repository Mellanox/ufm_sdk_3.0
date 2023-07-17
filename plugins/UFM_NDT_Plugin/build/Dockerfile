FROM ubuntu:20.04 AS ndt_base_ubuntu20

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG MOFED_VER=5.9-0.5.6.0
ARG MOFED_DIR=MLNX_OFED_LINUX-${MOFED_VER}-ubuntu20.04-x86_64

ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

LABEL maintainer="atolikin@nvidia.com"

RUN apt-get update && apt upgrade -y && apt-get -y install supervisor python3 python3-pip rsyslog mc wget vim libcap2 curl sudo

RUN python3 -m pip install flask flask_restful requests pandas twisted apscheduler "tzlocal<3.0"

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/


COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/ui_build.sh /
COPY config/ndt_httpd_proxy.conf config/ndt.conf config/ufm_plugin_ndt_httpd.conf config/ndt_ui_conf.json ${BASE_PATH}/

RUN /ui_build.sh

RUN echo "wget -q https://content.mellanox.com/ofed/MLNX_OFED-${MOFED_VER}/${MOFED_DIR}.tgz"
# Install OFED
RUN wget -q https://content.mellanox.com/ofed/MLNX_OFED-${MOFED_VER}/${MOFED_DIR}.tgz && \
    tar xf ${MOFED_DIR}.tgz && \
    rm -f ${MOFED_DIR}.tgz && \
    cd ${MOFED_DIR} && \
    ./mlnxofedinstall --without-fw-update --user-space-only --skip-distro-check --skip-unsupported-devices-check --force && \
    cd ../ && \
    rm -rf ${MOFED_DIR}

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
