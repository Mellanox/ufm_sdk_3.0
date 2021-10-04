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
      libtool \
      libtool-bin \
      glib2.0 \
      libnuma-dev \
      libcurl3-dev \
      libssl-dev \
      vim \
      libcap2 \
        && \
    apt clean all

# Install OFED
RUN wget -q https://content.mellanox.com/ofed/MLNX_OFED-${MOFED_VER}/${MOFED_DIR}.tgz && \
    tar xf ${MOFED_DIR}.tgz && \
    rm -f ${MOFED_DIR}.tgz && \
    cd ${MOFED_DIR} && \
    ./mlnxofedinstall --without-fw-update --user-space-only --skip-distro-check --skip-unsupported-devices-check --force && \
    cd ../ && \
    rm -rf ${MOFED_DIR}

# Install UCX-Py
COPY whl/ucx_py-0+unknown-cp36-cp36m-linux_x86_64.whl /tmp/ucx-py/
RUN python3 -m pip install requests numpy cython \
    /tmp/ucx-py/ucx_py-0+unknown-cp36-cp36m-linux_x86_64.whl

# Copy init.sh needed for manage_ufm_plugins.py script
COPY init.sh /init.sh

# Copy ufm_rdma.py and ufm_rdma.ini
COPY src ${BASE_PATH}

# Copy service record library
# TODO: need to copy source code and build it here
COPY lib ${BASE_PATH}

# TODO: temporary solution to check deplotment flow, replace it with ufm_rdma.py call
CMD ["/opt/ufm/ufm-plugin-ufm-rest/infinite_loop.sh"]