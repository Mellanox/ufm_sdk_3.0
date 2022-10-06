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
#
import logging
import subprocess
from enum import Enum
import os


class Constants:
    VERSION = '1.0.0'
    CONF_LOGFILE_NAME = 'log_file_name'
    UFM_HTTP_PORT = 443
    UFM_PLUGIN_PORT = 8008
    PLUGIN_HELP = f"This plugin version- {VERSION} is for getting rest apis from the UFM using grpc.\n" \
                  f"The plugin can send the rest api once or stream in intervals, " \
                  f"or even to subscribe to known client and receive all the data sending to that client.\n" \
                  f"To start create a session using CreateSession and add subscriber, with Addsubscriber." \
                  f"Then choose RunOnceJob - receive once rest api, RunStreamJob - receive stream of rest api or SubscribeToStream to subscribe to a client results.\n" \
                  f"Please see the proto file in protos for the full API."
    CONF_USERNAME = 'admin'
    CONF_PASSWORD = 'password'
    DEF_LOG_FILE = '/log/grpc_streamer_server.log'
    REST_URL_EVENTS = "/app/events"
    REST_URL_ALARMS = "/app/alarms"
    REST_URL_LINKS = "/app/links"
    REST_URL_JOBS = "/app/jobs"
    REST_DEFAULT_INTERVAL_LOW = 10
    REST_DEFAULT_INTERVAL_HIGH = 60

    UFM_GRPC_STREAMER_CONF_NAME = "ufm_grpc_streamer.conf"
    GRPC_STREAMER_DEF_PATH = "/etc/grpc_streamer"
    GRPC_STREAMER_SERVICE_PATH = "/lib/systemd/system/grpc_streamer.service"

    #config_file_name = "../build/config/grpc_streamer.conf"
    config_file_name = "config/grpc_streamer.conf"
    grpc_max_workers = 10
    log_level = logging.INFO
    log_file_backup_count = 5
    log_file_max_size = 100 * 100 * 1024

    LOG_SERVER_START = "Starting server with host %s"
    LOG_SERVER_STOP = "Stopping server with host %s"
    LOG_SERVER_HOST = "Config Server with host %s."
    LOG_CONNECT_UFM = "Connecting to UFM server, %s"
    LOG_NO_REST_SUBSCRIBER = "Cannot add new subscriber without any rest calls. check the RESTCall enum for all the rest api calls"
    LOG_CANNOT_UFM = 'Cannot connect to the ufm server. %s'
    LOG_CANNOT_SESSION = "Wasn't able to create session to the ufm, Connection Error, please see this exception.%s"
    LOG_CANNOT_SUBSCRIBER = "Cannot create subscriber. %s"
    LOG_CANNOT_NO_SESSION = "Server need a Session to the UFM to do this action, please use CreateSession"
    LOG_CREATE_SESSION = "Creating new session to the ufm. %s"
    LOG_CREATE_SUBSCRIBER = "Creating new subscriber: %s"
    LOG_EXISTED_SUBSCRIBER = "Already exists subscriber: %s"
    LOG_NO_EXIST_SUBSCRIBER = "No exists subscriber:%s"
    LOG_EDIT_SUBSCRIBER = "Editing an existing subscriber to new params.%s"
    LOG_DELETE_SUBSCRIBER = "Deleting subscriber. %s"
    LOG_LIST_SUBSCRIBER = "Get the list of existing subscribers."
    LOG_CALL_SERIALIZATION = "Called to do a serialization with all subscribers."
    LOG_CALL_STOP_STREAM = "Called to stop the stream of running job. %s"
    LOG_RUN_JOB_ONCE = "Called to extract api data from a job once. %s"
    LOG_RUN_JOB_Periodically = "Called to extract api data from a job periodically. %s"
    LOG_RUN_STREAM = "Called to run stream an api data from a new subscriber. %s"
    LOG_RUN_ONCE = "Called to run once an api data from a new subscriber. %s"
    LOG_CALL_SUBSCRIBE = "Called to subscribe to ID and stream data when a stream with that ID is used. %s"
    LOG_GET_PARAMS = "Called to get api params from a job. %s"
    LOG_CREATE_STREAM = "Configurate the stream with job. %s"
    LOG_START_STREAM = "String to stream job with threads. %s"
    LOG_STOP_STREAM = "Stopping stream because client stop connecting to the server. %s"
    ERROR_NO_SESSION = "Cant run client without session, please use CreateSession first. Need to create a session"
    ERROR_NO_CLIENT = "Cant run client without creating subscriber, please use AddSubscriber first."
    ERROR_NO_IP_FOUND = "CLIENT IP NOT FOUND, Cannot continue with the action."
    ERROR_CONNECTION = "Could not connect to the ufm and thus can send you messages"

    REST_DEFAULT_INTERVAL = 30
    REST_DEFAULT_DELTA = False


class GENERAL_UTILS:

    @staticmethod
    def run_cmd(command):
        proc = subprocess.Popen(command, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        stdout = stdout.decode("ascii")
        stderr = stderr.decode("ascii")
        return proc.returncode, str(stdout.strip()), str(stderr.strip())

    @staticmethod
    def getGrpcStreamConfFile():
        cmd = 'cat %s | grep ConditionPathExists' % Constants.GRPC_STREAMER_SERVICE_PATH
        ret, path, _ = GENERAL_UTILS.run_cmd(cmd)
        if ret == 0 and path:
            path = path.split('=')[1]
            return "%s/%s" % (os.path.dirname(path), Constants.UFM_GRPC_STREAMER_CONF_NAME)
        else:
            return "%s/%s" % (Constants.GRPC_STREAMER_DEF_PATH, Constants.UFM_GRPC_STREAMER_CONF_NAME)


class RESTCall(Enum):
    Events = (Constants.REST_URL_EVENTS, Constants.REST_DEFAULT_INTERVAL_LOW, True)
    Alarms = (Constants.REST_URL_ALARMS, Constants.REST_DEFAULT_INTERVAL_LOW, True)
    Links = (Constants.REST_URL_LINKS, Constants.REST_DEFAULT_INTERVAL_HIGH, False)
    Jobs = (Constants.REST_URL_JOBS, Constants.REST_DEFAULT_INTERVAL_HIGH, False)

    def __init__(self, extension, interval=10, delta=False):
        self.location = extension
        self.interval = interval
        self.delta = delta

    @classmethod
    def __contains__(cls, value):
        return value in cls._member_names_

