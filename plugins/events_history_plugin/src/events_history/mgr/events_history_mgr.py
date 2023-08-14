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


from utils.singleton import Singleton
import fnmatch
import os
import gzip
from utils.logger import Logger, LOG_LEVELS
from model.event import Event
from constants.events_constants import EventsConstants
import re


class EventsHistoryMgr(Singleton):
    """
    This class is designed to manage UFM events history
    """

    def __init__(self):

        self._events = EventsCollection(Event)
        self.parse_event_log_files()

    events = property(lambda self: self._events)

    def openEventFile(self, fname, mode):
        """
        Opens an event log file whether it is a compressed file or a regular one
        @param fname: the event log file name to be opened
        @param mode: a string indicating how the file is to be opened.
        @return: a reference to the opened file
        """
        try:
            if fname.endswith(".gz"):
                return gzip.open(fname, mode, encoding='utf8')
            else:
                return open(fname, mode)
        except FileNotFoundError:
            Logger.log_message(f"File {fname} not found.",
                               LOG_LEVELS.ERROR)

        except Exception as ex:
            Logger.log_message(f"An error occurred while parsing {fname}:" + str(ex),
                               LOG_LEVELS.ERROR)

    def parse_event_log_files(self):
        """
        This function is designed to parse the event log files and create an event if the event type is one of the topology change events.
        """
        try:
            # Gets all event log files
            files = fnmatch.filter(os.listdir(EventsConstants.EVENT_LOGS_DIRECTORY), EventsConstants.EVENT_LOG + "*.gz")
            files.append(EventsConstants.EVENT_LOG)
            for file in files:
                fname = os.path.join(EventsConstants.EVENT_LOGS_DIRECTORY, file)
                if os.path.exists(fname):
                    f = self.openEventFile(fname, 'rt')
                    if f:
                        for line in f:
                            self.create_event(line)
                        f.close()
        except Exception as e:
            Logger.log_message("Error occurred while parsing events logs files: " + str(e),
                               LOG_LEVELS.ERROR)

    def create_event(self, log_line):
        """
        This function is designed to create an event object from the given log line; the only accepted event is a topology change event.
        :param log_line: str, log line e.g. 2023-08-13 22:08:53.704 [45] [352] INFO [Logical_Model] Grid [Grid]: Network management is added
        :return:
        """
        try:
            match = re.search(EventsConstants.EVENT_LOG_PATTERN, log_line)
            if match:
                # Extract the variables from the match object
                time = match.group(EventsConstants.TIMESTAMP)
                id = match.group(EventsConstants.ID)
                event_type = match.group(EventsConstants.EVENT_TYPE)
                severity = match.group(EventsConstants.SEVERITY)
                category = match.group(EventsConstants.CATEGORY)
                object_name = match.group(EventsConstants.OBJECT_NAME)
                object_path = match.group(EventsConstants.OBJECT_PATH)
                description = match.group(EventsConstants.DESCRIPTION)
                #TODO extract event name, and add only the topology change events
                event = Event(timestamp=time, id=id, event_type=event_type, severity=severity,
                              category=category, object_name=object_name, object_path=object_path,
                              description=description, name="N/A")
                self.events.add(event)
        except Exception as ex:
            Logger.log_message(f"Error occurred while parsing event log line {log_line}: {str(ex)}",
                               LOG_LEVELS.ERROR)


class EventsCollection(dict):
    """
    This class represents a collection of UFM events history.
    """
    def __init__(self, typ):
        self.typ = typ

    def __call__(self, id=0):
        if id:
            return list(self.values()[id:])
        else:
            return list(self.values())

    def count(self):
        """return the number of element in the collection"""
        return len(self)

    def add(self, obj):
        """add event to the collection"""
        self[obj.id] = obj

    def remove(self, obj):
        """remove event from the collection"""
        del self[obj.id]




