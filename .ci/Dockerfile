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
    apt install -y python3 python3-pip apt-transport-https sqlite3 sudo git ca-certificates curl gnupg lsb-release software-properties-common expect ssh net-tools iputils-ping && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && \
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable" && \
    apt-get update && \
    apt-get install -y docker-ce-cli &&\
    env && \
    which ssh && \
    which expect 


RUN echo "${_LOGIN} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN echo "root ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN rm -rf /tmp/*
RUN cat /dev/null > ~/.bash_history
SHELL ["/bin/bash"]
WORKDIR /tmp




