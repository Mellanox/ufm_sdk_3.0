ARG ARCH
FROM nbu-harbor.gtm.nvidia.com/ufm/ufm_docker/ubuntu_base_${ARCH}_24_04:20260114 AS ndt_base_ubuntu24

# Will install ibutils2 of the same version as UFM base docker.
ARG _DOCA_VER=3.0.0
ARG _DOCA_BUILD_VER=058000
ARG _DOCA_REL_VER=25.04
ARG _DIST=ubuntu2404
# currently supported only x86_64. The reason of such arch is that for ubuntu24.04 doca installation
# extention not supporting classical arch values (aarch64 or x86_64 - output of "uname -m").
ARG _ARCH=amd64
ARG DOCA_URL=http://nbu-nfs.gtm.nvidia.com/auto/sw/release/doca/doca-host-repo/doca-repo-${_DOCA_VER}/doca-repo-${_DOCA_VER}-${_DOCA_BUILD_VER}/doca-host_${_DOCA_VER}-${_DOCA_BUILD_VER}-${_DOCA_REL_VER}-${_DIST}_${_ARCH}.deb
ARG UFM_DOCA_DEP="ibutils2"


ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

LABEL maintainer="atolikin@nvidia.com"

RUN apt-get update && apt upgrade -y && apt-get -y install supervisor python3 python3-pip rsyslog mc wget cron logrotate vim libcap2 curl sudo libtiff6

# Will install ibutils2 of the same version as UFM base docker.
RUN cd /tmp/ && wget --no-check-certificate ${DOCA_URL} && \
    dpkg -i doca-host_${_DOCA_VER}-${_DOCA_BUILD_VER}-${_DOCA_REL_VER}-${_DIST}_${_ARCH}.deb && \
    apt update && \
    apt install -y ${UFM_DOCA_DEP} && \
    rm -rf /tmp/doca-host*.deb && \
    apt-get purge doca-host -y && apt-get clean

RUN python3 -m pip install flask flask_restful requests pandas twisted apscheduler pyDes "tzlocal<3.0" --break-system-packages

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/
COPY ufm_sdk_tools/ ${BASE_PATH}/ufm_sdk_tools/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/ui_build.sh config/upgrade.sh /
COPY config/ndt_logrotate.conf /etc/logrotate.d/ndt
COPY config/ndt_httpd_proxy.conf config/ndt.conf config/ufm_plugin_ndt_httpd.conf config/ndt_ui_conf.json ${BASE_PATH}/

RUN /ui_build.sh

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
