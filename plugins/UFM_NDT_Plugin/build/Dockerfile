FROM ubuntu:20.04 AS ndt_base_ubuntu20

LABEL maintainer="atolikin@nvidia.com"
ARG _ARCH=x86_64
ARG _DIST=ubuntu20.04
ARG _OFED_VER=5.9-0.5.6.0
ARG OFED_URL=http://nbu-nfs.mellanox.com/auto/sw/release/mlnx_ofed/MLNX_OFED/MLNX_OFED_LINUX-${_OFED_VER}/MLNX_OFED_LINUX-${_OFED_VER}-${_DIST}-${_ARCH}/DEBS
ARG NDT_OFED_DEP="libibumad3 libibverbs1 ibverbs-providers "
ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

SHELL ["/bin/bash", "-c"]
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt upgrade -y && apt-get -y install supervisor python3 python3-pip rsyslog mc wget cron logrotate vim libcap2 curl sudo

RUN python3 -m pip install flask flask_restful requests pandas twisted apscheduler pyDes "tzlocal<3.0"

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/


COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/ui_build.sh /
COPY config/ndt_logrotate.conf /etc/logrotate.d/ndt
COPY config/ndt_httpd_proxy.conf config/ndt.conf config/ufm_plugin_ndt_httpd.conf config/ndt_ui_conf.json ${BASE_PATH}/

RUN /ui_build.sh

RUN echo "Download ibdiagnet (${NDT_OFED_DEP}}) from mofed (${_OFED_VER}}) repo" && \
    mkdir /tmp/ofed_temp && pushd /tmp/ofed_temp && \
    # mofed deb is not a proper repository so cannot be added as a repo but needs to be downloaded and installed manually \
    for pkg in ${NDT_OFED_DEP}; do \
        full_pkg_name=$(curl ${OFED_URL}/ 2>&1| sed -n "s/.*>\s*\(${pkg}_.*deb\)<.*/\1/p" ); \
        curl ${OFED_URL}/${full_pkg_name} -O; \
    done && \
    apt-get install -y ./* && \
    popd && \
    rm -rf /tmp/ofed_temp

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
