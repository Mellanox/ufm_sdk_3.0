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
# @date:   Aug 15, 2023
#

import os
from threading import Lock
import pyinotify
from utils.singleton import Singleton
from utils.logger import Logger, LOG_LEVELS


class AbstractFileWatcher(Singleton):
    """
    Base class for File Watching ,
    This Class should be extended and not used directly!
    Each derived class should can watch one or more files.

    Example of subclass can be found in infra.filewatch in file gvWatcher.py
    Note: this class was copied from UFM project
    """

    def __init__(self, file_list, events, read_freq=300):
        """
        :param file_list: list, list of paths to files the watcher will listen on
        :param events: list, list of events on the files that the watcher listens on taken from Events class (below this class)
        :param read_freq: int, is the interval between every time we request for the files that have been modified
        @ivar _watchedFileList: the list of files we want to watch
        @ivar _watchedDirs: the list of directories we want to watch
        @ivar _listener_list: the list of listeners to inform on file events
        @ivar _listener_id_counter: the id that the next listener will get
        @ivar _listener_data_lock: the lock being locked when adding/removing listeners
        """
        self._watchedFileList = set([os.path.abspath(f) for f in file_list])
        self._watchedDirs = set([os.path.dirname(f) for f in self._watchedFileList])
        self._listener_dict = {}
        self._listener_id_counter = 0
        self._listener_data_lock = Lock()
        self._startWatching(events, read_freq=read_freq)

    def _startWatching(self, events, read_freq):
        """
        Start file watching by the watch manager
        :param events: list of events on the files that the watcher listens on taken from Events class (below this class)
        """
        # initialize bitmask with all zeros (no events).
        mask = 0x00000000
        # Iterate through the list of events and add each event to the bitmask.
        # The '|' operator is used to perform a bitwise OR operation to combine event masks.
        for event in events:
            mask = mask | event
        try :
            wm = pyinotify.WatchManager()
            eh = EventHandler(self)
            self._notifier = pyinotify.ThreadedNotifier(wm, eh, read_freq=read_freq)

            for path in self._watchedDirs:
                wm.add_watch(path, mask)

            self._notifier.daemon = True
            self._notifier.start()

        except Exception as e:
            Logger.log_message("FileWatcher: Was NOT able to start, %s is NOT watched, the reason is : %s" % (self._watchedFileList, e), LOG_LEVELS.ERROR)
            return
        Logger.log_message("FileWatcher: %s is being watched " % self._watchedFileList, LOG_LEVELS.INFO)

    def __del__(self):
        """
        Stop file watching by the watch manager
        """
        if hasattr(self, '_notifier'):
            self._notifier.stop()
            Logger.log_message("FileWatcher: %s is NO LONGER being watched" % self._watchedFileList, LOG_LEVELS.INFO)

    def addListener(self, listener):
        """
        adds listener to the file watcher
        :param listener: the listener to add to the listeners list
        :return: the listener id
        """
        self._listener_data_lock.acquire()
        id = self._listener_id_counter
        self._listener_dict[id] = listener
        self._listener_id_counter += 1
        self._listener_data_lock.release()
        return id

    def removeListener(self, id):
        """
        removes listener from the file watcher by id given
        :param id: the id of the listener to remove
        :return: True if the listener was removed and false if no listener with the given id was found
        """
        try :
            self._listener_dict.pop(id)

        except :
            return False

        return True

    def handleEvent(self, event):
        if event.pathname in self._watchedFileList:
            #print "==> ", event.maskname, ": ", event.pathname
            # Invokes process_MASKNAME
            meth = getattr(self, 'process_' + event.maskname, None)
            if meth is not None:
                meth(event)

    """
    The methods below should be implemented by subclasses, each method deals with different event type (on files).
    for example, in this methods is where you will notify the listeners on the files of the event that happened.
    ** If you are watching more then one file, you can use the event object to get the file that caused the event. **
    """

    def process_IN_ACCESS(self, event):
        pass

    def process_IN_MODIFY(self, event):
        pass

    def process_IN_ATTRIB(self, event):
        pass

    def process_IN_CLOSE_WRITE(self, event):
        pass

    def process_IN_CLOSE_NOWRITE(self, event):
        pass

    def process_IN_OPEN(self, event):
        pass

    def process_IN_MOVED_FROM(self, event):
        pass

    def process_IN_MOVED_TO(self, event):
        pass

    def process_IN_CREATE(self, event):
        pass

    def process_IN_DELETE(self, event):
        pass

    def process_IN_DELETE_SELF(self, event):
        pass

    def process_IN_MOVE_SELF(self, event):
        pass

    def process_default(self, event):
        pass


class EventHandler(pyinotify.ProcessEvent):
    """
    This class handle specific actions when filesystem events occur.
    It's responsible for processing events such as file modifications, access, attribute changes, and more
    !!! This class should not be touched !!!
    """

    def __init__(self, fileWatcher):
        """
        @ivar _fw :
            The instance of the fileWatcher
        """
        self._fw = fileWatcher

    def process_default(self, event):
        """
        when an event type that doesn't have a specific method override is encountered. In other words, it serves
        as a catch-all method that gets called for any event type that doesn't have its own dedicated method defined
        in your custom event handler class.
        :param event: the data of the event that occurred(file name, mask name,..).
        :return:
        """
        self._fw.handleEvent(event)
