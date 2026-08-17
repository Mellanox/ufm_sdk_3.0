ARG ARCH
ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

# =============================================================================
# Stage 1: UI Builder - Build frontend assets
# =============================================================================
FROM node:16-slim AS ui-builder

ARG BASE_PATH

COPY ufm_sim_web_service/ndt-ui ${BASE_PATH}/ufm_sim_web_service/ndt-ui

WORKDIR ${BASE_PATH}/ufm_sim_web_service/ndt-ui

ARG OUTPUT_PATH=${BASE_PATH}/ufm_sim_web_service/media
RUN npm install --force && \
    node node_modules/@angular/cli/bin/ng build --output-path=${OUTPUT_PATH}

# =============================================================================
# Stage 2: Final Runtime Image
# =============================================================================
FROM nbu-harbor.gtm.nvidia.com/ufm/ufm_docker/ubuntu_base_${ARCH}_24_04:20260723 AS ndt_base_ubuntu24
ARG ARCH
ARG BASE_PATH

# Will install ibutils2 of the same version as UFM base docker.
ARG _DOCA_VER=3.0.0
ARG _DOCA_BUILD_VER=058000
ARG _DOCA_REL_VER=25.04
ARG _DIST=ubuntu2404
ARG UFM_DOCA_DEP="ibutils2"


ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

LABEL maintainer="atolikin@nvidia.com"

RUN apt-get update && apt upgrade -y && apt-get -y install supervisor python3 python3-pip rsyslog mc wget cron logrotate vim libcap2 libtiff6

# Will install ibutils2 of the same version as UFM base docker.
RUN set -eux; \
    case "$ARCH" in \
        aarch64) _ARCH=arm64 ;; \
        x86_64)  _ARCH=amd64 ;; \
        *) echo "Unsupported ARCH: $ARCH"; exit 1 ;; \
    esac; \
    DOCA_URL=http://nbu-nfs.gtm.nvidia.com/auto/sw/release/doca/doca-host-repo/doca-repo-${_DOCA_VER}/doca-repo-${_DOCA_VER}-${_DOCA_BUILD_VER}/doca-host_${_DOCA_VER}-${_DOCA_BUILD_VER}-${_DOCA_REL_VER}-${_DIST}_${_ARCH}.deb && \
    cd /tmp/ && wget --no-check-certificate ${DOCA_URL} && \
    dpkg -i doca-host_${_DOCA_VER}-${_DOCA_BUILD_VER}-${_DOCA_REL_VER}-${_DIST}_${_ARCH}.deb && \
    apt update && \
    apt install -y ${UFM_DOCA_DEP} && \
    rm -rf /tmp/doca-host*.deb && \
    apt-get purge doca-host -y && apt-get clean

RUN python3 -m pip install flask flask_restful requests pandas twisted apscheduler pyDes "tzlocal<3.0" --break-system-packages

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/
RUN rm -rf ${BASE_PATH}/ufm_sim_web_service/ndt-ui
COPY --from=ui-builder ${BASE_PATH}/ufm_sim_web_service/media ${BASE_PATH}/ufm_sim_web_service/media

COPY ufm_sdk_tools/ ${BASE_PATH}/ufm_sdk_tools/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh config/upgrade.sh /
COPY config/ndt_logrotate.conf /etc/logrotate.d/ndt
COPY config/ndt_httpd_proxy.conf config/ndt.conf config/ufm_plugin_ndt_httpd.conf config/ndt_ui_conf.json ${BASE_PATH}/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
