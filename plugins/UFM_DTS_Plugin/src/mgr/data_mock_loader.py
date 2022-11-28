#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Haitham Jondi
# @date:   Nov 23, 2022
#
from utils.singleton import Singleton
from mgr.data_model import DataModel


class DataMockLoader(Singleton):
    def __init__(self):
        self.dataModel = DataModel.getInstance()

    def set_data(self):
        host_name = "c-237-153-80-083-bf2"
        package_data = [
            {
                "package_name": "accountsservice",
                "version": "0.6.55-0ubuntu12~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "acpid",
                "version": "1:2.0.32-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "adduser",
                "version": "3.118ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "alien",
                "version": "8.95",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "alsa-topology-conf",
                "version": "1.2.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "alsa-ucm-conf",
                "version": "1.2.2-1ubuntu0.13",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "apparmor",
                "version": "2.13.3-7ubuntu5.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "apport",
                "version": "2.20.11-0ubuntu27.24",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "apport-symptoms",
                "version": "0.23",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "apt",
                "version": "2.0.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "apt-utils",
                "version": "2.0.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "at",
                "version": "3.1.23-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "autoconf",
                "version": "2.69-11.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "autofs",
                "version": "5.1.6-2ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "automake",
                "version": "1:1.16.1-4ubuntu6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "autopoint",
                "version": "0.19.8.1-10build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "autotools-dev",
                "version": "20180224.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "base-files",
                "version": "11ubuntu5.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "base-passwd",
                "version": "3.5.47",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bash",
                "version": "5.0-6ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bash-completion",
                "version": "1:2.10-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bc",
                "version": "1.07.1-2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bcache-tools",
                "version": "1.0.8-3ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bf-release",
                "version": "3.9.0",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bind9-dnsutils",
                "version": "1:9.16.1-0ubuntu2.10",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bind9-host",
                "version": "1:9.16.1-0ubuntu2.10",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bind9-libs",
                "version": "1:9.16.1-0ubuntu2.10",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "binutils",
                "version": "2.34-6ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "binutils-aarch64-linux-gnu",
                "version": "2.34-6ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "binutils-common",
                "version": "2.34-6ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bison",
                "version": "2:3.5.1+dfsg-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bolt",
                "version": "0.9.1-2~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bridge-utils",
                "version": "1.6-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bsdmainutils",
                "version": "11.1.2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bsdutils",
                "version": "1:2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "btrfs-progs",
                "version": "5.4.1-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "build-essential",
                "version": "12.8ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "busybox-initramfs",
                "version": "1:1.30.1-4ubuntu6.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "busybox-static",
                "version": "1:1.30.1-4ubuntu6.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "byobu",
                "version": "5.133-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "bzip2",
                "version": "1.0.8-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ca-certificates",
                "version": "20211016~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cloud-guest-utils",
                "version": "0.31-7-gd99b2d76-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cloud-init",
                "version": "22.2-0ubuntu1~20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cloud-initramfs-copymods",
                "version": "0.45ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cloud-initramfs-dyn-netconf",
                "version": "0.45ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cmake",
                "version": "3.16.3-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cmake-data",
                "version": "3.16.3-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "collectx-dpeserver",
                "version": "1.11.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "command-not-found",
                "version": "20.04.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "conntrack",
                "version": "1:1.4.5-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "console-setup",
                "version": "1.194ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "console-setup-linux",
                "version": "1.194ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "containerd",
                "version": "1.5.9-0ubuntu1~20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "coreutils",
                "version": "8.30-3ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cpio",
                "version": "2.13+dfsg-2ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cpp",
                "version": "4:9.3.0-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cpp-9",
                "version": "9.4.0-1ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cracklib-runtime",
                "version": "2.9.6-3.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "crda",
                "version": "3.18-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cri-tools",
                "version": "1.24.2-00",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cron",
                "version": "3.0pl1-136ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cryptsetup",
                "version": "2:2.2.2-3ubuntu2.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cryptsetup-bin",
                "version": "2:2.2.2-3ubuntu2.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cryptsetup-initramfs",
                "version": "2:2.2.2-3ubuntu2.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cryptsetup-run",
                "version": "2:2.2.2-3ubuntu2.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "curl",
                "version": "7.68.0-1ubuntu2.12",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "cython3",
                "version": "0.29.14-0.1ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dash",
                "version": "0.5.10.2-6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dbus",
                "version": "1.12.16-2ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dbus-user-session",
                "version": "1.12.16-2ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dc",
                "version": "1.07.1-2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dconf-gsettings-backend",
                "version": "0.36.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dconf-service",
                "version": "0.36.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "debconf",
                "version": "1.5.73",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "debconf-i18n",
                "version": "1.5.73",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "debhelper",
                "version": "12.10ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "debianutils",
                "version": "4.9.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "debugedit",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "device-tree-compiler",
                "version": "1.5.1-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "devio",
                "version": "1.2-1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dh-autoreconf",
                "version": "19",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dh-python",
                "version": "4.20191017ubuntu7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dh-strip-nondeterminism",
                "version": "1.7.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "diffutils",
                "version": "1:3.7-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dirmngr",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "distro-info",
                "version": "0.23ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "distro-info-data",
                "version": "0.43ubuntu1.10",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dmeventd",
                "version": "2:1.02.167-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dmidecode",
                "version": "3.2-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dmsetup",
                "version": "2:1.02.167-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dns-root-data",
                "version": "2019052802",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dnsmasq-base",
                "version": "2.80-1.1ubuntu1.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "doca-grpc",
                "version": "1.4.0079-1",
                "status": "deinstall ok config-files",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "doca-libs",
                "version": "1.4.0079-1",
                "status": "deinstall ok config-files",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "doca-prime-tools",
                "version": "1.4.0079-1",
                "status": "deinstall ok config-files",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "docker.io",
                "version": "20.10.12-0ubuntu2~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "docutils-common",
                "version": "0.16+dfsg-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dosfstools",
                "version": "4.1-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dpa-compiler",
                "version": "1.0.0",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dpcp",
                "version": "1.1.29-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dpkg",
                "version": "1.19.7ubuntu3.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dpkg-dev",
                "version": "1.19.7ubuntu3.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "dwz",
                "version": "0.13-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "e2fsprogs",
                "version": "1.45.5-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "eatmydata",
                "version": "105-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ebtables",
                "version": "2.0.11-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ed",
                "version": "1.16-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "efibootmgr",
                "version": "17-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "eject",
                "version": "2.1.5+deb1+cvs20081104-14",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ethtool",
                "version": "1:5.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fakeroot",
                "version": "1.24-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fdisk",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "file",
                "version": "1:5.38-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "finalrd",
                "version": "6~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "findutils",
                "version": "4.7.0-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "flash-kernel",
                "version": "3.103ubuntu1~20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "flex",
                "version": "2.6.4-6.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "flexio",
                "version": "0.5.850",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fontconfig",
                "version": "2.13.1-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fontconfig-config",
                "version": "2.13.1-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fonts-dejavu-core",
                "version": "2.37-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fonts-liberation",
                "version": "1:1.07.4-11",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fonts-ubuntu-console",
                "version": "0.83-4ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "freeipmi-common",
                "version": "1.6.4-3ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "friendly-recovery",
                "version": "0.2.41ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ftp",
                "version": "0.17-34.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fuse",
                "version": "2.9.9-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fwupd",
                "version": "1.7.5-3~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "fwupd-signed",
                "version": "1.27.1ubuntu7+1.2-2~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "g++",
                "version": "4:9.3.0-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "g++-9",
                "version": "9.4.0-1ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gawk",
                "version": "1:5.0.1+dfsg-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gcc",
                "version": "4:9.3.0-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gcc-10-base",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gcc-9",
                "version": "9.4.0-1ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gcc-9-base",
                "version": "9.4.0-1ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gdb",
                "version": "9.2-0ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gdbserver",
                "version": "9.2-0ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gdisk",
                "version": "1.0.5-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gettext",
                "version": "0.19.8.1-10build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gettext-base",
                "version": "0.19.8.1-10build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gir1.2-glib-2.0",
                "version": "1.64.1-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gir1.2-packagekitglib-1.0",
                "version": "1.1.13-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "git",
                "version": "1:2.25.1-1ubuntu3.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "git-man",
                "version": "1:2.25.1-1ubuntu3.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "glib-networking",
                "version": "2.64.2-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "glib-networking-common",
                "version": "2.64.2-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "glib-networking-services",
                "version": "2.64.2-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gnupg",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gnupg-l10n",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gnupg-utils",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpg",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpg-agent",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpg-wks-client",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpg-wks-server",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpgconf",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpgsm",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpgv",
                "version": "2.2.19-3ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gpio-mlxbf2-modules",
                "version": "1.0-0.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "graphviz",
                "version": "2.42.2-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "grep",
                "version": "3.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "groff-base",
                "version": "1.22.4-4build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "grub-common",
                "version": "2.04-1ubuntu26.15",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "grub-efi-arm64",
                "version": "2.04-1ubuntu44.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "grub-efi-arm64-bin",
                "version": "2.04-1ubuntu44.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "grub-efi-arm64-signed",
                "version": "1.167.2+2.04-1ubuntu44.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "grub2-common",
                "version": "2.04-1ubuntu26.15",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gsettings-desktop-schemas",
                "version": "3.36.0-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "gzip",
                "version": "1.10-0ubuntu4.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "hdparm",
                "version": "9.58+ds-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "hostname",
                "version": "3.23",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "htop",
                "version": "2.2.0-2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "hwdata",
                "version": "0.333-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "hyperscan",
                "version": "5.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "i2c-mlxbf-modules",
                "version": "1.0-0.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "i2c-tools",
                "version": "4.1-2build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ibacm",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ibutils2",
                "version": "2.1.1-0.151.MLNX20220720.gcd746c3.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ibverbs-providers",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ibverbs-utils",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ifenslave",
                "version": "2.9ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ifupdown",
                "version": "0.8.35ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "infiniband-diags",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "info",
                "version": "6.7.0.dfsg.2-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "init",
                "version": "1.57",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "init-system-helpers",
                "version": "1.57",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "initramfs-tools",
                "version": "0.136ubuntu6.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "initramfs-tools-bin",
                "version": "0.136ubuntu6.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "initramfs-tools-core",
                "version": "0.136ubuntu6.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "install-info",
                "version": "6.7.0.dfsg.2-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "intltool-debian",
                "version": "0.35.0+20060710.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iperf3",
                "version": "3.7-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ipmb-dev-int-modules",
                "version": "1.0-0.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ipmb-host-modules",
                "version": "1.0-0.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ipmitool",
                "version": "1.8.18-8",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iproute2",
                "version": "5.5.0-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iptables",
                "version": "1.8.4-3ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iptables-persistent",
                "version": "1.0.14ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iputils-arping",
                "version": "3:20190709-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iputils-ping",
                "version": "3:20190709-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iputils-tracepath",
                "version": "3:20190709-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "irqbalance",
                "version": "1.6.0-3ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "isc-dhcp-client",
                "version": "4.4.1-2.1ubuntu5.20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "isc-dhcp-common",
                "version": "4.4.1-2.1ubuntu5.20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iser-modules",
                "version": "5.7-OFED.5.7.1.0.2.1.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "isert-modules",
                "version": "5.7-OFED.5.7.1.0.2.1.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iso-codes",
                "version": "4.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "iw",
                "version": "5.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "javascript-common",
                "version": "11",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "jq",
                "version": "1.6-1ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "kbd",
                "version": "2.0.4-4ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "kernel-mft-modules",
                "version": "4.21.0-99.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "kexec-tools",
                "version": "1:2.0.18-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "keyboard-configuration",
                "version": "1.194ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "keyutils",
                "version": "1.6-6ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "klibc-utils",
                "version": "2.0.7-1ubuntu5.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "kmod",
                "version": "27-1ubuntu2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "knem",
                "version": "1.1.4.90mlnx1-OFED.5.6.0.1.6.1.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "knem-modules",
                "version": "1.1.4.90mlnx1-OFED.5.6.0.1.6.1.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "kpartx",
                "version": "0.8.3-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "krb5-locales",
                "version": "1.17-6ubuntu4.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "kubelet",
                "version": "1.24.3-00",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "kubernetes-cni",
                "version": "0.8.7-00",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "landscape-common",
                "version": "19.12-0ubuntu4.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "language-selector-common",
                "version": "0.204.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "less",
                "version": "551-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libaccountsservice0",
                "version": "0.6.55-0ubuntu12~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libacl1",
                "version": "2.2.53-6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libaio1",
                "version": "0.3.112-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libalgorithm-diff-perl",
                "version": "1.19.03-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libalgorithm-diff-xs-perl",
                "version": "0.04-6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libalgorithm-merge-perl",
                "version": "0.08-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libann0",
                "version": "1.1.2+doc-7build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libapparmor1",
                "version": "2.13.3-7ubuntu5.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libappstream4",
                "version": "0.12.10-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libapt-pkg6.0",
                "version": "2.0.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libarchive-cpio-perl",
                "version": "0.10-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libarchive-zip-perl",
                "version": "1.67-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libarchive13",
                "version": "3.4.0-2ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libargon2-1",
                "version": "0~20171227-0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libasan5",
                "version": "9.4.0-1ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libasn1-8-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libasound2",
                "version": "1.2.2-2.1ubuntu2.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libasound2-data",
                "version": "1.2.2-2.1ubuntu2.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libassuan0",
                "version": "2.5.3-7ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libatasmart4",
                "version": "0.19-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libatm1",
                "version": "1:2.5.1-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libatomic1",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libattr1",
                "version": "1:2.4.48-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libaudit-common",
                "version": "1:2.8.5-2ubuntu6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libaudit1",
                "version": "1:2.8.5-2ubuntu6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libbabeltrace1",
                "version": "1.5.8-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libbinutils",
                "version": "2.34-6ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblkid-dev",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblkid1",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev-crypto2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev-fs2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev-loop2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev-part-err2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev-part2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev-swap2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev-utils2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libblockdev2",
                "version": "2.23-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libbluetooth3",
                "version": "5.53-0ubuntu3.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libbrotli1",
                "version": "1.0.7-6ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libbsd-dev",
                "version": "0.10.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libbsd0",
                "version": "0.10.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libbz2-1.0",
                "version": "1.0.8-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libc-bin",
                "version": "2.31-0ubuntu9.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libc-dev-bin",
                "version": "2.31-0ubuntu9.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libc6",
                "version": "2.31-0ubuntu9.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libc6-dbg",
                "version": "2.31-0ubuntu9.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libc6-dev",
                "version": "2.31-0ubuntu9.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcairo2",
                "version": "1.16.0-4ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcanberra0",
                "version": "0.30-7ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcap-dev",
                "version": "1:2.32-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcap-ng0",
                "version": "0.7.9-2.1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcap2",
                "version": "1:2.32-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcap2-bin",
                "version": "1:2.32-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcbor0.6",
                "version": "0.6.0-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcc1-0",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcdt5",
                "version": "2.42.2-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcgraph6",
                "version": "2.42.2-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcom-err2",
                "version": "1.45.5-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libconfig9",
                "version": "1.5-0.4build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcrack2",
                "version": "2.9.6-3.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcroco3",
                "version": "0.6.13-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcrypt-dev",
                "version": "1:4.4.10-10ubuntu4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcrypt1",
                "version": "1:4.4.10-10ubuntu4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcryptsetup12",
                "version": "2:2.2.2-3ubuntu2.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libctf-nobfd0",
                "version": "2.34-6ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libctf0",
                "version": "2.34-6ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcurl3-gnutls",
                "version": "7.68.0-1ubuntu2.12",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libcurl4",
                "version": "7.68.0-1ubuntu2.12",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdatrie1",
                "version": "0.2.12-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdb5.3",
                "version": "5.3.28+dfsg1-0.6ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdbd-sqlite3-perl",
                "version": "1.64-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdbi-perl",
                "version": "1.643-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdbus-1-3",
                "version": "1.12.16-2ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdconf1",
                "version": "0.36.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdebconfclient0",
                "version": "0.251ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdebhelper-perl",
                "version": "12.10ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdevmapper-event1.02.1",
                "version": "2:1.02.167-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdevmapper1.02.1",
                "version": "2:1.02.167-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdns-export1109",
                "version": "1:9.11.16+dfsg-3~ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdoca-libs-dev",
                "version": "1.4.0079-1",
                "status": "deinstall ok config-files",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdpkg-perl",
                "version": "1.19.7ubuntu3.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libdw1",
                "version": "0.176-1.1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libeatmydata1",
                "version": "105-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libedit2",
                "version": "3.1-20191231-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libefiboot1",
                "version": "37-2ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libefivar1",
                "version": "37-2ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libelf-dev",
                "version": "0.176-1.1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libelf1",
                "version": "0.176-1.1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liberror-perl",
                "version": "0.17029-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libestr0",
                "version": "0.1.10-2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libev4",
                "version": "1:4.31-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libevent-2.1-7",
                "version": "2.1.11-stable-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libexpat1",
                "version": "2.2.9-1ubuntu0.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libexpat1-dev",
                "version": "2.2.9-1ubuntu0.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libext2fs2",
                "version": "1.45.5-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfakeroot",
                "version": "1.24-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfastjson4",
                "version": "0.99.8-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfdisk1",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfdt1",
                "version": "1.5.1-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libffi-dev",
                "version": "3.3-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libffi7",
                "version": "3.3-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfido2-1",
                "version": "1.3.1-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfile-fcntllock-perl",
                "version": "0.22-3build4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfile-stripnondeterminism-perl",
                "version": "1.7.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfl-dev",
                "version": "2.6.4-6.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfl2",
                "version": "2.6.4-6.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfontconfig1",
                "version": "2.13.1-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfreeipmi17",
                "version": "1.6.4-3ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfreetype6",
                "version": "2.10.1-2ubuntu0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfribidi0",
                "version": "1.0.8-2ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfuse2",
                "version": "2.9.9-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfwupd2",
                "version": "1.7.5-3~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfwupdplugin1",
                "version": "1.5.11-0ubuntu1~20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libfwupdplugin5",
                "version": "1.7.5-3~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgcab-1.0-0",
                "version": "1.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgcc-9-dev",
                "version": "9.4.0-1ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgcc-s1",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgcrypt20",
                "version": "1.8.5-5ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgd3",
                "version": "2.2.5-5.2ubuntu2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgdbm-compat4",
                "version": "1.18.1-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgdbm6",
                "version": "1.18.1-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgirepository-1.0-1",
                "version": "1.64.1-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libglib2.0-0",
                "version": "2.64.6-1~ubuntu20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libglib2.0-bin",
                "version": "2.64.6-1~ubuntu20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libglib2.0-data",
                "version": "2.64.6-1~ubuntu20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libglib2.0-dev",
                "version": "2.64.6-1~ubuntu20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libglib2.0-dev-bin",
                "version": "2.64.6-1~ubuntu20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgmp10",
                "version": "2:6.2.0+dfsg-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgnutls30",
                "version": "3.6.13-2ubuntu1.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgomp1",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgpg-error0",
                "version": "1.37-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgpgme11",
                "version": "1.13.1-7ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgpm2",
                "version": "1.20.7-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgraphite2-3",
                "version": "1.3.13-11build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgrpc-dev",
                "version": "1.39.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgssapi-krb5-2",
                "version": "1.17-6ubuntu4.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgssapi3-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgstreamer1.0-0",
                "version": "1.16.2-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgts-0.7-5",
                "version": "0.7.6+darcs121130-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgts-bin",
                "version": "0.7.6+darcs121130-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgudev-1.0-0",
                "version": "1:233-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgusb2",
                "version": "0.3.4-0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgvc6",
                "version": "2.42.2-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libgvpr2",
                "version": "2.42.2-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libharfbuzz0b",
                "version": "2.6.4-1ubuntu4.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libhcrypto4-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libheimbase1-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libheimntlm0-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libhogweed5",
                "version": "3.5.1+really3.5.1-2ubuntu0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libhugetlbfs-bin",
                "version": "2.22-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libhx509-5-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libi2c0",
                "version": "4.1-2build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libibmad-dev",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libibmad5",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libibnetdisc5",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libibumad-dev",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libibumad3",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libibverbs-dev",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libibverbs1",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libice6",
                "version": "2:1.0.10-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libicu66",
                "version": "66.1-2ubuntu2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libidn11",
                "version": "1.33-2.2ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libidn2-0",
                "version": "2.2.0-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libimagequant0",
                "version": "2.12.2-1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libip4tc2",
                "version": "1.8.4-3ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libip6tc2",
                "version": "1.8.4-3ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libiperf0",
                "version": "3.7-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libisc-export1105",
                "version": "1:9.11.16+dfsg-3~ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libiscsi7",
                "version": "1.18.0-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libisl22",
                "version": "0.22.1-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libisns0",
                "version": "0.97-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libitm1",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjansson-dev",
                "version": "2.12-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjansson4",
                "version": "2.12-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjbig0",
                "version": "2.1-3.1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjcat1",
                "version": "0.1.4-0ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjpeg-turbo8",
                "version": "2.0.3-0ubuntu1.20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjpeg8",
                "version": "8c-2ubuntu8",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjq1",
                "version": "1.6-1ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjs-jquery",
                "version": "3.3.1~dfsg-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjs-sphinxdoc",
                "version": "1.8.5-7ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjs-underscore",
                "version": "1.9.1~dfsg-1ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjson-c-dev",
                "version": "0.13.1+dfsg-7ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjson-c4",
                "version": "0.13.1+dfsg-7ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjson-glib-1.0-0",
                "version": "1.4.4-2ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjson-glib-1.0-common",
                "version": "1.4.4-2ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libjsoncpp1",
                "version": "1.7.4-3.1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libk5crypto3",
                "version": "1.17-6ubuntu4.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libkeyutils1",
                "version": "1.6-6ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libklibc",
                "version": "2.0.7-1ubuntu5.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libkmod2",
                "version": "27-1ubuntu2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libkrb5-26-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libkrb5-3",
                "version": "1.17-6ubuntu4.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libkrb5support0",
                "version": "1.17-6ubuntu4.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libksba8",
                "version": "1.3.5-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblab-gamut1",
                "version": "2.42.2-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblcms2-2",
                "version": "2.9-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libldap-2.4-2",
                "version": "2.4.49+dfsg-2ubuntu1.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libldap-common",
                "version": "2.4.49+dfsg-2ubuntu1.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblmdb0",
                "version": "0.9.24-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblocale-gettext-perl",
                "version": "1.07-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblsan0",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libltdl-dev",
                "version": "2.4.6-14",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libltdl7",
                "version": "2.4.6-14",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblua5.2-0",
                "version": "5.2.4-1.1build3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblvm2cmd2.03",
                "version": "2.03.07-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblz4-1",
                "version": "1.9.2-2ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblzma-dev",
                "version": "5.2.4-1ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblzma5",
                "version": "5.2.4-1ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liblzo2-2",
                "version": "2.10-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmagic-mgc",
                "version": "1:5.38-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmagic1",
                "version": "1:5.38-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmail-sendmail-perl",
                "version": "0.80-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmaxminddb0",
                "version": "1.4.2-0ubuntu1.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmbim-glib4",
                "version": "1.26.2-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmbim-proxy",
                "version": "1.26.2-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmm-glib0",
                "version": "1.18.6-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmnl-dev",
                "version": "1.0.4-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmnl0",
                "version": "1.0.4-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmount-dev",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmount1",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmpc3",
                "version": "1.1.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmpdec2",
                "version": "2.4.2-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmpfr6",
                "version": "4.0.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libmysqlclient21",
                "version": "8.0.30-0ubuntu0.20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libncurses6",
                "version": "6.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libncursesw6",
                "version": "6.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libndp0",
                "version": "1.7-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnetfilter-conntrack3",
                "version": "1.0.7-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnetplan0",
                "version": "0.104-0ubuntu2~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnettle7",
                "version": "3.5.1+really3.5.1-2ubuntu0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnewt0.52",
                "version": "0.52.21-4ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnfnetlink0",
                "version": "1.0.1-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnfsidmap2",
                "version": "0.25-5.1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnftnl11",
                "version": "1.1.5-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnghttp2-14",
                "version": "1.40.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnghttp2-dev",
                "version": "1.40.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnl-3-200",
                "version": "3.4.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnl-3-dev",
                "version": "3.4.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnl-genl-3-200",
                "version": "3.4.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnl-route-3-200",
                "version": "3.4.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnl-route-3-dev",
                "version": "3.4.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnm0",
                "version": "1.22.10-1ubuntu2.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnpth0",
                "version": "1.6-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnspr4",
                "version": "2:4.25-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnss-systemd",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnss3",
                "version": "2:3.49.1-1ubuntu1.8",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libntfs-3g883",
                "version": "1:2017.3.23AR.3-3ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnuma-dev",
                "version": "2.0.12-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libnuma1",
                "version": "2.0.12-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libogg0",
                "version": "1.3.4-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libonig5",
                "version": "6.9.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libopensm",
                "version": "5.12.0.MLNX20220721.3a88a9b-0.1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libopensm-devel",
                "version": "5.12.0.MLNX20220721.3a88a9b-0.1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libopenvswitch",
                "version": "2.17.2-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libossp-uuid16",
                "version": "1.6.2-1.5build7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libp11-kit0",
                "version": "0.23.20-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpackagekit-glib2-18",
                "version": "1.1.13-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpam-cap",
                "version": "1:2.32-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpam-modules",
                "version": "1.3.1-5ubuntu4.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpam-modules-bin",
                "version": "1.3.1-5ubuntu4.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpam-pwquality",
                "version": "1.4.2-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpam-runtime",
                "version": "1.3.1-5ubuntu4.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpam-systemd",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpam0g",
                "version": "1.3.1-5ubuntu4.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpango-1.0-0",
                "version": "1.44.7-2ubuntu4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpangocairo-1.0-0",
                "version": "1.44.7-2ubuntu4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpangoft2-1.0-0",
                "version": "1.44.7-2ubuntu4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpaper-utils",
                "version": "1.1.28",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpaper1",
                "version": "1.1.28",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libparted-fs-resize0",
                "version": "3.3-4ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libparted2",
                "version": "3.3-4ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpathplan4",
                "version": "2.42.2-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcap-dev",
                "version": "1.9.1-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcap0.8",
                "version": "1.9.1-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcap0.8-dev",
                "version": "1.9.1-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpci3",
                "version": "1:3.6.4-1ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre16-3",
                "version": "2:8.39-12ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre2-16-0",
                "version": "10.34-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre2-32-0",
                "version": "10.34-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre2-8-0",
                "version": "10.34-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre2-dev",
                "version": "10.34-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre2-posix2",
                "version": "10.34-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre3",
                "version": "2:8.39-12ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre3-dev",
                "version": "2:8.39-12ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcre32-3",
                "version": "2:8.39-12ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcrecpp0v5",
                "version": "2:8.39-12ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpcsclite1",
                "version": "1.8.26-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libperl5.30",
                "version": "5.30.0-9ubuntu0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpipeline1",
                "version": "1.5.2-2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpixman-1-0",
                "version": "0.38.4-0ubuntu2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpka1",
                "version": "1.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpng16-16",
                "version": "1.6.37-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpolkit-agent-1-0",
                "version": "0.105-26ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpolkit-gobject-1-0",
                "version": "0.105-26ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpopt0",
                "version": "1.16-14",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libprocps8",
                "version": "2:3.3.16-1ubuntu2.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libproxy1v5",
                "version": "0.4.15-10ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpsl5",
                "version": "0.21.0-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpwquality-common",
                "version": "1.4.2-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpwquality1",
                "version": "1.4.2-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython2.7-minimal",
                "version": "2.7.18-1~20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython2.7-stdlib",
                "version": "2.7.18-1~20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython3-dev",
                "version": "3.8.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython3-stdlib",
                "version": "3.8.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython3.8",
                "version": "3.8.10-0ubuntu1~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython3.8-dev",
                "version": "3.8.10-0ubuntu1~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython3.8-minimal",
                "version": "3.8.10-0ubuntu1~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libpython3.8-stdlib",
                "version": "3.8.10-0ubuntu1~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libqmi-glib5",
                "version": "1.30.4-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libqmi-proxy",
                "version": "1.30.4-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librdmacm-dev",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librdmacm1",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libreadline5",
                "version": "5.2+dfsg-3build3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libreadline8",
                "version": "8.0-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librhash0",
                "version": "1.3.9-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libroken18-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librpm8",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librpmbuild8",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librpmio8",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librpmsign8",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librtmp1",
                "version": "2.4+20151223.gitfa8646d.1-2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "librxpcompiler-dev",
                "version": "22.05.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsasl2-2",
                "version": "2.1.27+dfsg-2ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsasl2-modules",
                "version": "2.1.27+dfsg-2ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsasl2-modules-db",
                "version": "2.1.27+dfsg-2ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsctp1",
                "version": "1.0.18+dfsg-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libseccomp2",
                "version": "2.5.1-1ubuntu1~20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libselinux1",
                "version": "3.0-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libselinux1-dev",
                "version": "3.0-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsemanage-common",
                "version": "3.0-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsemanage1",
                "version": "3.0-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsensors-config",
                "version": "1:3.6.0-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsensors5",
                "version": "1:3.6.0-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsepol1",
                "version": "3.0-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsepol1-dev",
                "version": "3.0-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsgutils2-2",
                "version": "1.44-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsigsegv2",
                "version": "2.12-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libslang2",
                "version": "2.3.2-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsm6",
                "version": "2:1.2.3-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsmartcols1",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsnmp-base",
                "version": "5.8+dfsg-2ubuntu2.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsnmp35",
                "version": "5.8+dfsg-2ubuntu2.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsodium23",
                "version": "1.0.18-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsoup2.4-1",
                "version": "2.70.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsqlite3-0",
                "version": "3.31.1-4ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libss2",
                "version": "1.45.5-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libssh-4",
                "version": "0.9.3-2ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libssl-dev",
                "version": "1.1.1f-1ubuntu2.16",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libssl1.1",
                "version": "1.1.1f-1ubuntu2.16",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libstdc++-9-dev",
                "version": "9.4.0-1ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libstdc++6",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libstemmer0d",
                "version": "0+svn585-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsub-override-perl",
                "version": "0.09-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsys-hostname-long-perl",
                "version": "1.5-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsystemd-dev",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libsystemd0",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtasn1-6",
                "version": "4.16.0-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtcl8.6",
                "version": "8.6.10+dfsg-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtdb1",
                "version": "1.4.3-0ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libteamdctl0",
                "version": "1.30-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtext-charwidth-perl",
                "version": "0.04-10",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtext-iconv-perl",
                "version": "1.7-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtext-wrapi18n-perl",
                "version": "0.06-9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libthai-data",
                "version": "0.1.28-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libthai0",
                "version": "0.1.28-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtiff5",
                "version": "4.1.0+git191117-2ubuntu0.20.04.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtinfo6",
                "version": "6.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtirpc-common",
                "version": "1.2.5-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtirpc3",
                "version": "1.2.5-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtool",
                "version": "2.4.6-14",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtsan0",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libtss2-esys0",
                "version": "2.3.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libubsan1",
                "version": "10.3.0-1ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libuchardet0",
                "version": "0.0.6-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libudev-dev",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libudev1",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libudisks2-0",
                "version": "2.8.4-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libunbound-dev",
                "version": "1.9.4-2ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libunbound8",
                "version": "1.9.4-2ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libunistring2",
                "version": "0.9.10-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libunwind-dev",
                "version": "1.2.1-9build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libunwind8",
                "version": "1.2.1-9build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liburcu6",
                "version": "0.11.1-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liburing1",
                "version": "0.7-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liburiparser-dev",
                "version": "0.9.3-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "liburiparser1",
                "version": "0.9.3-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libusb-1.0-0",
                "version": "2:1.0.23-2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libutempter0",
                "version": "1.1.6-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libuuid1",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libuv1",
                "version": "1.34.2-1ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libvma",
                "version": "9.6.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libvma-dev",
                "version": "9.6.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libvma-utils",
                "version": "9.6.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libvolume-key1",
                "version": "0.3.12-3.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libvorbis0a",
                "version": "1.3.6-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libvorbisfile3",
                "version": "1.3.6-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libwebp6",
                "version": "0.6.1-2ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libwebpdemux2",
                "version": "0.6.1-2ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libwebpmux3",
                "version": "0.6.1-2ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libwind0-heimdal",
                "version": "7.7.0+dfsg-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libwrap0",
                "version": "7.6.q-30",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libx11-6",
                "version": "2:1.6.9-2ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libx11-data",
                "version": "2:1.6.9-2ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxau6",
                "version": "1:1.0.9-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxaw7",
                "version": "2:1.0.13-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxcb-render0",
                "version": "1.14-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxcb-shm0",
                "version": "1.14-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxcb1",
                "version": "1.14-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxdmcp6",
                "version": "1:1.1.3-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxext6",
                "version": "2:1.3.4-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxlio",
                "version": "1.3.5-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxlio-dev",
                "version": "1.3.5-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxlio-utils",
                "version": "1.3.5-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxml2",
                "version": "2.9.10+dfsg-5ubuntu0.20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxmlb1",
                "version": "0.1.15-2ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxmu6",
                "version": "2:1.1.3-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxmuu1",
                "version": "2:1.1.3-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxpm4",
                "version": "1:3.5.12-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxrender1",
                "version": "1:0.9.10-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxt6",
                "version": "1:1.1.5-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libxtables12",
                "version": "1.8.4-3ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libyaml-0-2",
                "version": "0.2.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libzip-dev",
                "version": "1.5.1-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libzip5",
                "version": "1.5.1-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "libzstd1",
                "version": "1.4.4+dfsg-3ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-base",
                "version": "4.5ubuntu3.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-bluefield",
                "version": "5.4.0.1042.41",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-bluefield-headers-5.4.0-1042",
                "version": "5.4.0-1042.47",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-bluefield-tools-5.4.0-1042",
                "version": "5.4.0-1042.47",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-headers-5.4.0-1042-bluefield",
                "version": "5.4.0-1042.47",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-headers-bluefield",
                "version": "5.4.0.1042.41",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-image-5.4.0-1042-bluefield",
                "version": "5.4.0-1042.47",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-image-bluefield",
                "version": "5.4.0.1042.41",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-libc-dev",
                "version": "5.4.0-123.139",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-modules-5.4.0-1042-bluefield",
                "version": "5.4.0-1042.47",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-tools-5.4.0-1042-bluefield",
                "version": "5.4.0-1042.47",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-tools-bluefield",
                "version": "5.4.0.1042.41",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linux-tools-common",
                "version": "5.4.0-123.139",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "linuxptp",
                "version": "1.9.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lldpad",
                "version": "1.0.1+git20200210.2022b0c-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lm-sensors",
                "version": "1:3.6.0-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "locales",
                "version": "2.31-0ubuntu9.9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "login",
                "version": "1:4.8.1-1ubuntu5.20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "logrotate",
                "version": "3.14.0-4ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "logsave",
                "version": "1.45.5-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lsb-base",
                "version": "11.1.0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lsb-release",
                "version": "11.1.0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lshw",
                "version": "02.18.85-0.3ubuntu2.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lsof",
                "version": "4.93.2+dfsg-1ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ltrace",
                "version": "0.7.3-6.1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lvm2",
                "version": "2.03.07-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lxd-agent-loader",
                "version": "0.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "lz4",
                "version": "1.9.2-2ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "m4",
                "version": "1.4.18-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "make",
                "version": "4.2.1-1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "man-db",
                "version": "2.9.1-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "manpages",
                "version": "5.05-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "manpages-dev",
                "version": "5.05-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mawk",
                "version": "1.3.4.20200120-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mdadm",
                "version": "4.1-5ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "meson",
                "version": "0.61.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mft",
                "version": "4.21.0-99",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mft-oem",
                "version": "4.21.0-99",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mime-support",
                "version": "3.64ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-dpdk",
                "version": "20.11.0-5.2.2.571020.5.2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-dpdk-dev",
                "version": "20.11.0-5.2.2.571020.5.2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-ethtool",
                "version": "5.18-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-fw-updater",
                "version": "5.7-1.0.2.0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-iproute2",
                "version": "5.18.0-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-libsnap",
                "version": "1.4.1-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-nvme-modules",
                "version": "5.7-OFED.5.7.1.0.2.1.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-ofed-kernel-modules",
                "version": "5.7-OFED.5.7.1.0.2.1.bf.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-ofed-kernel-utils",
                "version": "5.7-OFED.5.7.1.0.2.1.bf.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-snap",
                "version": "3.6.1-7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlnx-tools",
                "version": "5.2.0-0.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlocate",
                "version": "0.26-3ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlx-bootctl-modules",
                "version": "1.3-0.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlx-libopenipmi0",
                "version": "2.0.25-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlx-openipmi",
                "version": "2.0.25-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlx-regex",
                "version": "1.2-ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlxbf-bootctl",
                "version": "2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlxbf-bootimages",
                "version": "3.9.2-12271",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlxbf-gige-modules",
                "version": "1.0-0.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mlxbf-scripts",
                "version": "3.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "modemmanager",
                "version": "1.18.6-1~ubuntu20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mokutil",
                "version": "0.3.0+1538710437.fb6250f-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "motd-news-config",
                "version": "11ubuntu5.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mount",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mstflint",
                "version": "4.16.1-2.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mtd-utils",
                "version": "1:2.1.1-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mtr-tiny",
                "version": "0.93-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "multipath-tools",
                "version": "0.8.3-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "mysql-common",
                "version": "5.8+1.0.5ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "nano",
                "version": "4.8-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ncurses-base",
                "version": "6.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ncurses-bin",
                "version": "6.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ncurses-term",
                "version": "6.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "net-tools",
                "version": "1.60+git20180626.aebd88e-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "netbase",
                "version": "6.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "netcat-openbsd",
                "version": "1.206-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "netfilter-persistent",
                "version": "1.0.14ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "netplan.io",
                "version": "0.104-0ubuntu2~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "network-manager",
                "version": "1.22.10-1ubuntu2.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "network-manager-pptp",
                "version": "1.2.8-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "networkd-dispatcher",
                "version": "2.1-2~ubuntu20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "nfs-common",
                "version": "1:1.3.4-2.5ubuntu3.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ninja-build",
                "version": "1.10.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "nis",
                "version": "3.17.1-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ntfs-3g",
                "version": "1:2017.3.23AR.3-3ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "nvme-cli",
                "version": "1.9-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ofed-scripts",
                "version": "5.7-OFED.5.7.1.0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "open-iscsi",
                "version": "2.0.874-7.1ubuntu6.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "opensm",
                "version": "5.12.0.MLNX20220721.3a88a9b-0.1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "openssh-client",
                "version": "1:8.2p1-4ubuntu0.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "openssh-server",
                "version": "1:8.2p1-4ubuntu0.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "openssh-sftp-server",
                "version": "1:8.2p1-4ubuntu0.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "openssl",
                "version": "1.1.1f-1ubuntu2.16",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "openvswitch-common",
                "version": "2.17.2-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "openvswitch-ipsec",
                "version": "2.17.2-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "openvswitch-switch",
                "version": "2.17.2-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "opof",
                "version": "1.0.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "os-prober",
                "version": "1.74ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "overlayroot",
                "version": "0.45ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "packagekit",
                "version": "1.1.13-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "packagekit-tools",
                "version": "1.1.13-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pandoc",
                "version": "2.5-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pandoc-data",
                "version": "2.5-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "parted",
                "version": "3.3-4ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "passwd",
                "version": "1:4.8.1-1ubuntu5.20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pastebinit",
                "version": "1.5.1-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "patch",
                "version": "2.7.6-6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pci.ids",
                "version": "0.0~2020.03.20-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pciutils",
                "version": "1:3.6.4-1ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "perftest",
                "version": "4.5-0.17.g6f25f23.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "perl",
                "version": "5.30.0-9ubuntu0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "perl-base",
                "version": "5.30.0-9ubuntu0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "perl-modules-5.30",
                "version": "5.30.0-9ubuntu0.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pigz",
                "version": "2.4-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pinentry-curses",
                "version": "1.1.0-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pkg-config",
                "version": "0.29.1-0ubuntu4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "po-debconf",
                "version": "1.0.21",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "policykit-1",
                "version": "0.105-26ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pollinate",
                "version": "4.33-3ubuntu1.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "popularity-contest",
                "version": "1.69ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "powermgmt-base",
                "version": "1.36",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ppp",
                "version": "2.4.7-2+4.1ubuntu5.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pptp-linux",
                "version": "1.10.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "procps",
                "version": "2:3.3.16-1ubuntu2.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "psmisc",
                "version": "23.3-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "publicsuffix",
                "version": "20200303.0012-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "pwr-mlxbf-modules",
                "version": "1.0-0.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python-apt-common",
                "version": "2.0.0ubuntu0.20.04.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python-babel-localedata",
                "version": "2.6.0+dfsg.1-1ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python-pip-whl",
                "version": "20.0.2-5ubuntu1.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python2.7",
                "version": "2.7.18-1~20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python2.7-minimal",
                "version": "2.7.18-1~20.04.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3",
                "version": "3.8.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-alabaster",
                "version": "0.7.8-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-all",
                "version": "3.8.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-apport",
                "version": "2.20.11-0ubuntu27.24",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-apt",
                "version": "2.0.0ubuntu0.20.04.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-attr",
                "version": "19.3.0-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-automat",
                "version": "0.8.0-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-babel",
                "version": "2.6.0+dfsg.1-1ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-blinker",
                "version": "1.4+dfsg1-0.3ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-certifi",
                "version": "2019.11.28-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-cffi-backend",
                "version": "1.14.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-chardet",
                "version": "3.0.4-4build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-click",
                "version": "7.0-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-colorama",
                "version": "0.4.3-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-commandnotfound",
                "version": "20.04.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-configobj",
                "version": "5.0.6-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-constantly",
                "version": "15.1.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-cryptography",
                "version": "2.8-3ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-dbus",
                "version": "1.2.16-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-debconf",
                "version": "1.5.73",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-debian",
                "version": "0.1.36ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-dev",
                "version": "3.8.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-distro",
                "version": "1.4.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-distro-info",
                "version": "0.23ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-distupgrade",
                "version": "1:20.04.38",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-distutils",
                "version": "3.8.10-0ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-docutils",
                "version": "0.16+dfsg-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-entrypoints",
                "version": "0.3-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-gdbm",
                "version": "3.8.10-0ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-gi",
                "version": "3.36.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-hamcrest",
                "version": "1.9.0-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-httplib2",
                "version": "0.14.0-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-hyperlink",
                "version": "19.0.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-idna",
                "version": "2.8-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-imagesize",
                "version": "1.2.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-importlib-metadata",
                "version": "1.5.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-incremental",
                "version": "16.10.1-3.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-jinja2",
                "version": "2.10.1-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-json-pointer",
                "version": "2.0-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-jsonpatch",
                "version": "1.23-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-jsonschema",
                "version": "3.2.0-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-jwt",
                "version": "1.7.1-2ubuntu2.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-keyring",
                "version": "18.0.1-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-launchpadlib",
                "version": "1.10.13-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-lazr.restfulclient",
                "version": "0.14.2-2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-lazr.uri",
                "version": "1.0.3-4build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-lib2to3",
                "version": "3.8.10-0ubuntu1~20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-markupsafe",
                "version": "1.1.0-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-minimal",
                "version": "3.8.2-0ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-more-itertools",
                "version": "4.2.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-nacl",
                "version": "1.3.0-5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-netifaces",
                "version": "0.10.4-1ubuntu4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-newt",
                "version": "0.52.21-4ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-oauthlib",
                "version": "3.1.0-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-olefile",
                "version": "0.46-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-openssl",
                "version": "19.0.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-openvswitch",
                "version": "2.17.2-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-packaging",
                "version": "20.3-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pexpect",
                "version": "4.6.0-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pil",
                "version": "7.0.0-4ubuntu0.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pip",
                "version": "20.0.2-5ubuntu1.6",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pkg-resources",
                "version": "45.2.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-problem-report",
                "version": "2.20.11-0ubuntu27.24",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-protobuf",
                "version": "3.17.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-ptyprocess",
                "version": "0.6.0-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pyasn1",
                "version": "0.4.2-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pyasn1-modules",
                "version": "0.2.1-0.2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pyelftools",
                "version": "0.26-1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pygments",
                "version": "2.3.1+dfsg-1ubuntu2.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pymacaroons",
                "version": "0.13.0-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pyparsing",
                "version": "2.4.6-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pyrsistent",
                "version": "0.15.5-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-pyverbs",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-requests",
                "version": "2.22.0-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-requests-unixsocket",
                "version": "0.2.0-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-roman",
                "version": "2.0.0-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-secretstorage",
                "version": "2.3.1-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-serial",
                "version": "3.4-5.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-service-identity",
                "version": "18.1.0-5build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-setuptools",
                "version": "45.2.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-simplejson",
                "version": "3.16.0-2ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-six",
                "version": "1.14.0-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-software-properties",
                "version": "0.99.9.8",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-sphinx",
                "version": "1.8.5-7ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-systemd",
                "version": "234-3build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-twisted",
                "version": "18.9.0-11ubuntu0.20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-twisted-bin",
                "version": "18.9.0-11ubuntu0.20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-tz",
                "version": "2019.3-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-update-manager",
                "version": "1:20.04.10.10",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-urllib3",
                "version": "1.25.8-2ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-wadllib",
                "version": "1.3.3-3build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-wheel",
                "version": "0.34.2-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-yaml",
                "version": "5.3.1-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-zipp",
                "version": "1.0.0-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3-zope.interface",
                "version": "4.7.1-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3.8",
                "version": "3.8.10-0ubuntu1~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3.8-dev",
                "version": "3.8.10-0ubuntu1~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "python3.8-minimal",
                "version": "3.8.10-0ubuntu1~20.04.5",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rasdaemon",
                "version": "0.6.5-1ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rdma-core",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rdmacm-utils",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "read-edid",
                "version": "3.0.2-1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "readline-common",
                "version": "8.0-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rpcbind",
                "version": "1.2.5-8",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rpm",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rpm-common",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rpm2cpio",
                "version": "4.14.2.1+dfsg1-1build2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rsync",
                "version": "3.1.3-8ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rsyslog",
                "version": "8.2001.0-1ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "run-one",
                "version": "1.17-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "runc",
                "version": "1.1.0-0ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rxp-compiler",
                "version": "22.05.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "rxpbench",
                "version": "22.07.0",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sbsigntool",
                "version": "0.9.2-2ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "screen",
                "version": "4.8.0-1ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sed",
                "version": "4.7-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sensible-utils",
                "version": "0.0.12+nmu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sg3-utils",
                "version": "1.44-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sg3-utils-udev",
                "version": "1.44-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sgml-base",
                "version": "1.29.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "shared-mime-info",
                "version": "1.15-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "shim-signed",
                "version": "1.40.7+15.4-0ubuntu9",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "socat",
                "version": "1.7.3.3-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "software-properties-common",
                "version": "0.99.9.8",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sosreport",
                "version": "4.3-1ubuntu0.20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sound-theme-freedesktop",
                "version": "0.8-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "spdk",
                "version": "22.05-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "spdk-dev",
                "version": "22.05-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "spdk-rpc",
                "version": "22.05-4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sphinx-common",
                "version": "1.8.5-7ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sqlite3",
                "version": "3.31.1-4ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "srp-modules",
                "version": "5.7-OFED.5.7.1.0.2.1.kver.5.4.0-1042-bluefield",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "srptools",
                "version": "56mlnx40-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ssh-import-id",
                "version": "5.10-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "strace",
                "version": "5.5-3ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "strongswan",
                "version": "5.9.6-2bf",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "strongswan-swanctl",
                "version": "5.9.6-2bf",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sudo",
                "version": "1.8.31-1ubuntu1.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "systemd",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "systemd-sysv",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "systemd-timesyncd",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "sysvinit-utils",
                "version": "2.96-2.1ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "tar",
                "version": "1.30+dfsg-7ubuntu0.20.04.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "tcpdump",
                "version": "4.9.3-4ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "telnet",
                "version": "0.17-41.2build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "thin-provisioning-tools",
                "version": "0.8.5-4build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "time",
                "version": "1.7-25.1build1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "tmux",
                "version": "3.0a-2ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "tpm-udev",
                "version": "0.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "tzdata",
                "version": "2022a-0ubuntu0.20.04",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "u-boot-tools",
                "version": "2021.01+dfsg-3ubuntu0~20.04.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ubuntu-advantage-tools",
                "version": "27.9~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ubuntu-fan",
                "version": "0.12.13ubuntu0.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ubuntu-keyring",
                "version": "2020.02.11.4",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ubuntu-minimal",
                "version": "1.450.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ubuntu-release-upgrader-core",
                "version": "1:20.04.38",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ubuntu-server",
                "version": "1.450.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ubuntu-standard",
                "version": "1.450.2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ucf",
                "version": "3.0038+nmu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ucx",
                "version": "1.14.0-1.57102",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "udev",
                "version": "245.4-4ubuntu3.18",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "udisks2",
                "version": "2.8.4-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "ufw",
                "version": "0.36-6ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "unattended-upgrades",
                "version": "2.3ubuntu0.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "unzip",
                "version": "6.0-25ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "update-manager-core",
                "version": "1:20.04.10.10",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "update-notifier-common",
                "version": "3.192.30.11",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "usb-modeswitch",
                "version": "2.5.2+repack0-2ubuntu3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "usb-modeswitch-data",
                "version": "20191128-3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "usb.ids",
                "version": "2020.03.19-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "usbutils",
                "version": "1:012-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "util-linux",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "uuid",
                "version": "1.6.2-1.5build7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "uuid-dev",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "uuid-runtime",
                "version": "2.34-0.1ubuntu9.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "valgrind",
                "version": "1:3.15.0-1ubuntu9.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "vim",
                "version": "2:8.1.2269-1ubuntu5.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "vim-common",
                "version": "2:8.1.2269-1ubuntu5.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "vim-runtime",
                "version": "2:8.1.2269-1ubuntu5.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "vim-tiny",
                "version": "2:8.1.2269-1ubuntu5.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "virtio-net-controller",
                "version": "1.3.10-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "wamerican",
                "version": "2018.04.16-1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "watchdog",
                "version": "5.15-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "wget",
                "version": "1.20.3-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "whiptail",
                "version": "0.52.21-4ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "wireless-regdb",
                "version": "2022.06.06-0ubuntu1~20.04.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "wpasupplicant",
                "version": "2:2.9-1ubuntu4.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "x11-common",
                "version": "1:7.7+19ubuntu14",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "xauth",
                "version": "1:1.1-0ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "xdg-user-dirs",
                "version": "0.17-2ubuntu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "xfsprogs",
                "version": "5.3.0-1ubuntu2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "xkb-data",
                "version": "2.29-2",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "xml-core",
                "version": "0.18+nmu1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "xxd",
                "version": "2:8.1.2269-1ubuntu5.7",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "xz-utils",
                "version": "5.2.4-1ubuntu1.1",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "zlib1g",
                "version": "1:1.2.11.dfsg-2ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            },
            {
                "package_name": "zlib1g-dev",
                "version": "1:1.2.11.dfsg-2ubuntu1.3",
                "status": "install ok installed",
                "active": True,
                "deleted": False,
                "timestamp": 1669109712.649396,
                "hostname": "c-237-153-80-083-bf2"
            }
        ]
        self.dataModel.add_package_info(host_name, package_data)
