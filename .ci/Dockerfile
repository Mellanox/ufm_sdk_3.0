FROM ubuntu:20.04
ARG _ARCH=x86_64
ARG _UID=6213
ARG _GID=101
ARG _LOGIN=swx-jenkins
ARG _HOME=/var/home/$_LOGIN
RUN mkdir -p $_HOME
RUN groupadd -f -g "$_GID" "$_LOGIN"
RUN useradd -u "$_UID" -g "$_GID" -s /bin/bash -m -d ${_HOME} "$_LOGIN"
RUN chown $_LOGIN $_HOME
USER root

ENV TZ=Israel
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt clean && \
    apt update && \
    apt upgrade -y && \
    apt install -y python3 python3-pip apt-transport-https sqlite3 sudo git ca-certificates curl gnupg lsb-release software-properties-common && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && \
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable" && \
    apt-get update && \
    apt-get install -y docker-ce-cli

RUN echo "ufm-appliance04,10.209.36.63 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDP+RwBY3YDKRmcpZR8pSenGusCSKRZ3SDfq9ert7JWhP1dHpr3/2xzZwCcNBZ1Cl5VyKxzDAsXE62TU7r9DXRFRq0BrSo6qoPWvRVQTxI8RkOSeb8k5uBPckNo/FwTq/4EKR23msxcpNxoyswqAD91VPWScu9TtXlCiG2hqgAye+9j0f0Agp/eOfGPJcfzJqR0Q5ou2gcD5xo8/LevXhd4Mio7QJXo1RVUZUKNmDG0/MS1XFJdE6+NyCSs4Os+wMTB0UtW8TEzgFS2xpfvS0aueOTBvmJ90RQqkbLWhd+EfFdtQ03f8xZcqL1OjxWZ81c0Fd07ieKJpGgDZuOpqsGUgFb5diagpDaF/+xQ4Ciudw/IfxzolgI5ureYlA8IMb4NQe2DdNoXj4wk0cxTnmwl7rFviCDf++avicQmQdOrRwpRK2vYonw+ediDOCX473gupux0c2WoEv6Pv1vK8LYPCxt7t/GUxNtxx/bsOZc7tQf63eUdqvUv6+qcZxPPClM=" >> ~/.ssh/known_hosts

RUN echo "${_LOGIN} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN echo "root ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN rm -rf /tmp/*
RUN cat /dev/null > ~/.bash_history
SHELL ["/bin/bash"]
WORKDIR /tmp




