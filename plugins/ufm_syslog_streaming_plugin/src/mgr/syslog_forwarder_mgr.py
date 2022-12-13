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
# @author: Anan Al-Aghbar
# @date:   Oct 2, 2022
#
import time
import socket
from utils.flask_server import call_in_thread
from utils.logger import Logger, LOG_LEVELS
from utils.utils import Utils
from mgr.fluent_bit_service_mgr import FluentBitServiceMgr


class SyslogForwarder:

    def __init__(self, conf, socket_type=socket.SOCK_DGRAM,
                 bufmax=1 * 1024 * 1024):

        self.conf = conf
        self.socket_type = socket_type
        self.bufmax = bufmax
        self.ufm_syslog_host = None
        self.ufm_syslog_port = None
        self.fluent_bit_client_port = None
        self.remote_syslog_host = None
        self.remote_syslog_port = None
        #####

        self.ufm_syslog_socket = self.remote_syslog_socket = self.remote_syslog_address = None

    def _create_host_socket(self, ip, port, socket_type):
        # for IPv6
        # family = socket.AF_INET6
        # for IPv4
        # family = socket.AF_INET
        # for TCP
        # socket.SOCK_STREAM
        # proto = 6 => IPPROTO_TCP
        # for UPD
        # socket.SOCK_DGRAM
        # proto = 17 => IPPROTO_UCP
        addr_family = socket.AF_INET6 if Utils.is_ipv6_address(ip) else socket.AF_INET
        ip_info = socket.getaddrinfo(host=ip, port=port, type=socket_type)
        ip_socket = ip_data = None
        for _ip_data in ip_info:
            _addr_family, socket_type, protocol, _, addr = _ip_data
            if _addr_family == addr_family:
                ip_socket = socket.socket(addr_family, socket_type)
                ip_data = _ip_data
                break
        return ip_data, ip_socket

    def _create_ufm_syslog_socket(self):
        Logger.log_message(f'Creating the UFM syslog server on: {self.ufm_syslog_host}:{self.ufm_syslog_port}',
                           LOG_LEVELS.DEBUG)
        try:
            # create UFM syslog listener socket
            host_info, server_socket = self._create_host_socket(self.ufm_syslog_host, self.ufm_syslog_port, self.socket_type)
            _addr_family, socket_type, protocol, _, addr = host_info
            # if you need to reuse the port in case the port in use by different process uncomment
            # the below line
            # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(addr)
            Logger.log_message(f'The UFM syslog server created successfully on: {self.ufm_syslog_host}:{self.ufm_syslog_port}')
            return server_socket
        except Exception as ex:
            Logger.log_message(f'Error occurred during creating the UFM syslog server: {str(ex)}')

    def _create_remote_syslog_socket(self):
        Logger.log_message(f'Creating the External syslog client on: '
                           f'{self.remote_syslog_host}:{self.remote_syslog_port}', LOG_LEVELS.DEBUG)
        if self.remote_syslog_host:
            try:
                remote_syslog_host_info, remote_syslog_socket = self._create_host_socket(self.remote_syslog_host,
                                                                                         self.remote_syslog_port,
                                                                                         self.socket_type)
                _addr_family, socket_type, protocol, _, remote_syslog_address = remote_syslog_host_info
                Logger.log_message(f'The External syslog client created successfully on: '
                                   f'{self.remote_syslog_host}:{self.remote_syslog_port}')
                return remote_syslog_socket, remote_syslog_address
            except Exception as ex:
                Logger.log_message(f'Error occurred during creating the External syslog client on '
                                   f'{self.remote_syslog_host}:{self.remote_syslog_port}: {str(ex)}',
                                   LOG_LEVELS.ERROR)
                return None, None

    def check_fluent_destination(self):
        host = self.conf.get_fluent_bit_destination_host()
        port = self.conf.get_fluent_bit_destination_port()
        try:
            host_info, host_socket = self._create_host_socket(host,
                                                              port,
                                                              self.socket_type)
            return host_info
        except Exception as ex:
            Logger.log_message(f'Error occurred during creating the fluent-bit destination client on '
                               f'{host}:{port} : {str(ex)}',
                               LOG_LEVELS.ERROR)

    def streaming_is_enabled(self):
        return (self.conf.get_enable_sys_log_destination_flag() or self.conf.get_enable_fluent_bit_flag()) \
               and self.conf.get_enable_streaming_flag()

    def setup_forwarding_params(self):
        self.ufm_syslog_host = self.conf.get_ufm_syslog_host()
        self.ufm_syslog_port = self.conf.get_ufm_syslog_port()
        self.fluent_bit_client_port = self.conf.get_fluent_bit_src_port()
        self.remote_syslog_host = self.conf.get_sys_log_destination_host()
        self.remote_syslog_port = self.conf.get_syslog_destination_port()

    def setup(self):
        self.setup_forwarding_params()
        #####
        if not self.ufm_syslog_socket:
            self.ufm_syslog_socket = self._create_ufm_syslog_socket()
        #####
        if self.ufm_syslog_socket:
            if self.conf.get_enable_sys_log_destination_flag():
                self.remote_syslog_socket, self.remote_syslog_address = self._create_remote_syslog_socket()
            else:
                Logger.log_message('The syslog remote destination host is not enabled or configured',
                                   LOG_LEVELS.WARNING)
            #####
            if self.conf.get_enable_fluent_bit_flag():
                if self.check_fluent_destination():
                    self.conf.update_fluent_bit_conf_file()
                    result, _ = FluentBitServiceMgr.restart_service()
                    if result:
                        Logger.log_message(f'The fluent-bit streaming created successfully on the destination: '
                                           f'{self.conf.get_fluent_bit_destination_host()}:{self.conf.get_fluent_bit_destination_port()}')
                else:
                    FluentBitServiceMgr.stop_service()
            else:
                Logger.log_message('The fluent-bit destination host is not enabled or configured', LOG_LEVELS.WARNING)
                is_running, _ = FluentBitServiceMgr.get_service_status()
                if is_running:
                    FluentBitServiceMgr.stop_service()

    def restart_forwarding(self, restart_ufm_syslog_server=True):
        self.stop_forwarding(restart_ufm_syslog_server)
        self.start_forwarding()

    def start_forwarding(self):
        self.setup()
        call_in_thread(self.start_forwarding_thread)

    def start_forwarding_thread(self):
        while self.streaming_is_enabled() and self.ufm_syslog_socket:
            try:
                message, address = self.ufm_syslog_socket.recvfrom(self.bufmax)
                if self.remote_syslog_socket and self.remote_syslog_address:
                    self.remote_syslog_socket.sendto(message, self.remote_syslog_address)
                if self.ufm_syslog_socket and self.fluent_bit_client_port:
                    self.ufm_syslog_socket.sendto(message, ('127.0.0.1', self.fluent_bit_client_port))
            except Exception as ex:
                Logger.log_message(f'Error occurred during forwarding the logs to the destinations: {str(ex)}',
                                   LOG_LEVELS.ERROR)

    def stop_forwarding(self, restart_ufm_syslog_server=True):
        try:
            if self.ufm_syslog_socket and restart_ufm_syslog_server:
                self.ufm_syslog_socket.close()
                self.ufm_syslog_socket = None
                Logger.log_message('The UFM syslogs server is stopped')
            if self.remote_syslog_socket:
                self.remote_syslog_socket.close()
                self.remote_syslog_socket = None
                self.remote_syslog_address = None
                Logger.log_message('The streaming to remote syslogs client is stopped')
            if not self.conf.get_enable_fluent_bit_flag() and self.ufm_syslog_socket is None:
                is_running, _ = FluentBitServiceMgr.get_service_status()
                if is_running:
                    result, _ = FluentBitServiceMgr.stop_service()
                    if result:
                        Logger.log_message('The streaming client on fluent-bit is stopped')

        except Exception as ex:
            Logger.log_message(f'Error occurred during stopping the forwarding: {str(ex)}',
                               LOG_LEVELS.ERROR)
