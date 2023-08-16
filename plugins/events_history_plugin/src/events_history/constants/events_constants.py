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

from enum import Enum


class EventTypeEnum(Enum):
    LINK_IS_UP = '328'
    LINK_IS_DOWN = '329'
    Node_IS_UP = '332'
    Node_IS_DOWN = '331'
    SWITCH_IS_UP = '908'
    SWITCH_IS_DOWN = '907'
    DIRECTOR_SWITCH_IS_UP = '910'
    DIRECTOR_SWITCH_IS_DOWN = '909'


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
    EVENT_LOG_PATTERN = r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.*\d*) \[(?P<id>\d+)\] \[(?P<event_type>\d+)\] (?P<severity>\w+)( Site \[.+?\])? \[(?P<category>.+?)\] (?P<type>\w+) \[(?P<object_path>.+?)\]( \[dev_id:?(?P<object_name>.+?)\])?.*?: (?P<description>.+)"
    EVENT_LOGS_DIRECTORY = '/log'
    EVENT_LOG = "event.log"

    EVENTS_INFO = {
        EventTypeEnum.LINK_IS_UP.value: {
            "name":"Link is Up",
        },
        EventTypeEnum.LINK_IS_DOWN.value: {
            "name": "Link is Down",
        },
        EventTypeEnum.Node_IS_UP.value: {
            "name": "Node is Up",
        },
        EventTypeEnum.Node_IS_DOWN.value: {
            "name": "Node is Down",
        },
        EventTypeEnum.SWITCH_IS_UP.value: {
            "name": "Switch is Up",
        },
        EventTypeEnum.SWITCH_IS_DOWN.value: {
            "name": "Switch is Down",
        },
        EventTypeEnum.DIRECTOR_SWITCH_IS_UP.value: {
            "name": "Director Switch is Up",
        },
        EventTypeEnum.DIRECTOR_SWITCH_IS_DOWN.value: {
            "name": "Director Switch is Down",
        },

    }

