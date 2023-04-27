FROM ubuntu:20.04 AS pdr_base_ubuntu20

ENV TZ=Israel
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

LABEL maintainer="drorl@nvidia.com"

ARG BASE_PATH=/opt/ufm/ufm_plugin_pdr_deterministic
ARG CONF_PATH=${BASE_PATH}/conf
ARG SCRIPTS_PATH=${BASE_PATH}/scripts

EXPOSE 8000
EXPOSE 8982
EXPOSE 443

RUN apt-get update && apt-get -y install supervisor python3 python3-pip rsyslog vim curl sudo

RUN python3 -m pip install flask flask_restful requests urllib3 twisted jsonschema pandas

COPY ufm_sim_web_service/ ${BASE_PATH}/ufm_sim_web_service/

COPY config/supervisord.conf /etc/supervisor/conf.d/
COPY config/init.sh config/deinit.sh /
COPY config/pdr_deterministic.conf ${CONF_PATH}/
COPY config/pdr_deterministic_shared_volumes.conf ${CONF_PATH}/
COPY config/Field_BER_Thresholds.csv ${CONF_PATH}/
COPY config/fec_mode_lookup.json ${CONF_PATH}/
COPY scripts/init_pdr_conf.sh ${SCRIPTS_PATH}/
COPY utils/ ${BASE_PATH}/utils/

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
