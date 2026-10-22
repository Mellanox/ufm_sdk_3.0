from utils.filewatch.abstract_file_watcher import AbstractFileWatcher
import pyinotify
from utils.logger import Logger, LOG_LEVELS
from mgr.events_history_mgr import EventsHistoryMgr
from constants.events_constants import EventsConstants
import os


class EventsHistoryListener():
    """
    Listen for changes in files
    """
    # The last_position is used to read only the newly added lines in the log file by updating the pointer to that
    # position each time the file is read.

    def __init__(self):
        self.last_position = self._get_last_position()
        self.event_mgr = EventsHistoryMgr.getInstance()

    def onChange(self, event):
        """
        Called whenever a modification has been monitored by the watcher
        :param event: the data of the event that occurred(file name, mask name,..).
        :return:
        """
        with open(event.pathname) as log_file:
            log_file.seek(self.last_position)
            new_lines = log_file.readlines()
            self.last_position = log_file.tell()  # Update last position

            for line in new_lines:
                # Process each new line here
                self.event_mgr.create_event(line)

    def _get_last_position(self):
        file_path = os.path.join(EventsConstants.EVENT_LOGS_DIRECTORY, EventsConstants.EVENT_LOG)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_lines = f.readlines()
                return f.tell()
        except Exception as e:
            Logger.log_message(f"Error while getting the last opsition in {file_path}: {e}", LOG_LEVELS.ERROR)


class EventsHistoryFilesWatcher(AbstractFileWatcher):
    """
    This class is responsible for monitoring which files have been modified by listening to the IN_MODIFY events
    provided by the pyinotify library.
    """
    def __init__(self, files_list, read_freq=0):
        """
        :param files_list: list, is the list of files that we want to listen to when a change
        :param read_freq: int, is the interval between every time we request for the files that have been modified
        """
        events_list = [pyinotify.IN_MODIFY]
        super(EventsHistoryFilesWatcher, self).__init__(files_list, events_list, read_freq=read_freq)

    def notifyListeners(self, event):
        """
        This function is designed notify the listeners that a file has been modified
        :param event: the data of the event that occurred(file name, mask name,..).
        :return:
        """
        for listener in self._listener_dict.values():
            listener.onChange(event)

    def process_IN_MODIFY(self, event):
        """
        Notify listeners that a file has been modified.
        This function will be called when the event of a file modification (IN_MODIFY event) occurs
        :param event: the event that occurred.
        """
        Logger.log_message(f"event: {event}", LOG_LEVELS.DEBUG)
        self.notifyListeners(event)
