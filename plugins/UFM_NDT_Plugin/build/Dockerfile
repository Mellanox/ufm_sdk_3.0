FROM ubuntu:18.04 AS ndt_base_ubuntu18

ARG BASE_PATH=/opt/ufm/ufm_plugin_ndt

LABEL maintainer="nahum@nvidia.com"

# Install python3.
RUN apt-get update && apt-get -y install supervisor python3 python3-pip

# Python3 packages
RUN python3 -m pip install flask flask_restful requests

ADD ufm_sim_web_service ${BASE_PATH}/ufm_sim_web_service
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY init.sh /init.sh

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
