FROM ubuntu:18.04 AS ufm_rest_base_ubuntu18

ARG MOFED_VER=5.4-1.0.3.0
ARG MOFED_DIR=MLNX_OFED_LINUX-${MOFED_VER}-ubuntu18.04-x86_64
ARG BASE_PATH=/opt/ufm/ufm-plugin-ufm-rest

LABEL maintainer="atolikin@nvidia.com"

# Install general prerequisites
RUN apt-get update && \
    apt-get -y install \
      libfile-find-rule-perl-perl \
      wget \
        && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      perl \
      python3-dev \
      python3-pip \
      git \
      supervisor \
      libtool \
      libtool-bin \
      glib2.0 \
      libnuma-dev \
      libcurl3-dev \
      libssl-dev \
      vim \
      iproute2 \
      libcap2 \
        && \
    apt clean all


ADD src/ufm_rdma ${BASE_PATH}/src
ADD src/service_record /tmp/service_record
ADD src/common /tmp/common


COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN mkdir -p /opt/ufm/files/conf/plugins/rest-rdma
COPY src/ufm_rdma/ufm_rdma.ini /tmp/ufm_rdma.ini
COPY docker_init.sh /usr/sbin/docker_init.sh
COPY scripts/ufm_rest_rdma_client.sh ${BASE_PATH}/ufm_rest_rdma_client.sh

# Install OFED
RUN wget -q https://content.mellanox.com/ofed/MLNX_OFED-${MOFED_VER}/${MOFED_DIR}.tgz && \
    tar xf ${MOFED_DIR}.tgz && \
    rm -f ${MOFED_DIR}.tgz && \
    cd ${MOFED_DIR} && \
    ./mlnxofedinstall --without-fw-update --user-space-only --skip-distro-check --skip-unsupported-devices-check --force && \
    cd ../ && \
    rm -rf ${MOFED_DIR}

# Install UCX-Py and additional whl packages
COPY whl/ucx_py-0.23.0a0+21.g5cf86fc-cp36-cp36m-linux_x86_64.whl /tmp/ucx-py/

RUN python3 -m pip install --trusted-host swx-repos.mtr.labs.mlnx \
   -i http://swx-repos.mtr.labs.mlnx:8081/repository/ufm-py3-ubuntu1804/simple \
   pyOpenSSL

RUN python3 -m pip install setuptools-rust requests numpy cython asyncio \
    /tmp/ucx-py/ucx_py-0.23.0a0+21.g5cf86fc-cp36-cp36m-linux_x86_64.whl

# Copy init.sh needed for manage_ufm_plugins.py script
COPY init.sh /init.sh

# compile SRlib and copy to ${BASE_PATH}
COPY install_deps.sh /install_deps.sh
RUN /install_deps.sh /tmp/service_record /tmp/ready_sr_lib
RUN cp /tmp/ready_sr_lib/libservice_record_wrapper.so ${BASE_PATH}/src/

ENTRYPOINT ["sh", "/usr/sbin/docker_init.sh"]
