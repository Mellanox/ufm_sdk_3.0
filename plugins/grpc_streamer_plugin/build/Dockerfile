FROM ubuntu:20.04 AS ndt_base_ubuntu20

ENV TZ=Israel
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

LABEL maintainer="egershon@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_grpc_streamer

EXPOSE 8008
EXPOSE 443

RUN apt-get update && apt-get -y install supervisor python3 python3-pip rsyslog vim curl net-tools iproute2

RUN python3 -m pip install flask flask_restful requests grpcio twisted urllib3
RUN python3 -m pip install -IV protobuf==3.18.0

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh /
COPY config/grpc-streamer.conf config/grpc-streamer_shared_volumes.conf ${BASE_PATH}/


CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
