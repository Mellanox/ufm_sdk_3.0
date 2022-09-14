FROM ubuntu:20.04 AS ndt_base_ubuntu20

ARG BASE_PATH=/opt/ufm/ufm_plugin_gRPC_streamer

LABEL maintainer="egershon@nvidia.com"


ENV TZ=Israel
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get -y install supervisor python3 python3-pip rsyslog mc

RUN python3 -m pip install flask flask_restful requests grpcio twisted urllib3

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/

CMD ["python3", "./"]
