FROM ubuntu:20.04 AS bright_plugin_base_ubuntu20

LABEL maintainer="anana@nvidia.com"

ARG DEBIAN_FRONTEND=noninteractive
ARG BASE_PATH=/opt/ufm/ufm_plugin_bright
ARG SRC_BASE_DIR=bright_plugin

COPY ${SRC_BASE_DIR}/ ${BASE_PATH}/${SRC_BASE_DIR}/
COPY utils/ ${BASE_PATH}/utils/

COPY ${SRC_BASE_DIR}/conf/supervisord.conf /etc/supervisor/conf.d/
COPY ${SRC_BASE_DIR}/scripts/init.sh ${SRC_BASE_DIR}/scripts/deinit.sh /

RUN apt-get update && apt-get -y install supervisor python3.9 python3-pip vim curl sudo

RUN python3.9 -m pip install -r ${BASE_PATH}/${SRC_BASE_DIR}/src/bright/requirements.txt

# remove an unused library that caused a high CVE vulnerability issue https://redmine.mellanox.com/issues/3621850
RUN apt-get remove -y linux-libc-dev

RUN ${BASE_PATH}/${SRC_BASE_DIR}/scripts/install_pythoncm.sh

RUN ${BASE_PATH}/${SRC_BASE_DIR}/scripts/ui_build.sh

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
