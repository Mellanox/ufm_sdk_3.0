FROM ubuntu:latest

ARG BASE_PATH=/opt/ufm/ufm-plugin-ndt
ENV PYTHONPATH=${BASE_PATH}/src

LABEL maintainer="nahum@nvidia.com"
# Install python3.

RUN apt-get update && apt-get -y install supervisor python3 python3-pip

# Python3 packages
RUN pip3 install flask flask_restful

ADD src ${BASE_PATH}/src
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY init.sh /init.sh

RUN python3 -m compileall -b ${BASE_PATH}/src/ufm_sim
#RUN find ${BASE_PATH}/src/ufm_sim -type f -name "*.py" -delete

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
