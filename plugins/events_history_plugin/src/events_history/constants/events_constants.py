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
# @author: Abeer Moghrabi
# @date:   Aug 9, 2023
#

class EventsConstants:
    ID = "id"
    NAME = "name"
    TYPE = "type"
    EVENT_TYPE = "event_type"
    SEVERITY = "severity"
    TIMESTAMP = "timestamp"
    COUNTER = "counter"
    CATEGORY = "category"
    OBJECT_NAME = "object_name"
    OBJECT_PATH = "object_path"
    WRITE_TO_SYSLOG = "write_to_syslog"
    DESCRIPTION = "description"
    EVENT_LOG_PATTERN = r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.*\d*) \[(?P<id>\d+)\] \[(?P<event_type>\d+)\] (?P<severity>\w+) \[(?P<category>.+?)\] (?P<object_name>\w+) \[(?P<object_path>\w+)\]: (?P<description>.+)"
    EVENT_LOGS_DIRECTORY = '/log'
    EVENT_LOG = "event.log"
