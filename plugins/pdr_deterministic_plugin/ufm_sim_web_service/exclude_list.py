#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import time
import threading

class ExcludeListItem:
    """
    Represents details of excluded port.

    Attributes:
        port_name (str): The name of the port.
        ttl_seconds (int): Time interval to live in exclude list in seconds (0 - forever).
        remove_time (int): Absolute time to remove from exclude list (0 - never remove).
    """
    def __init__(self, port_name, ttl_seconds):
        """
        Initialize a new instance of the ExcludeListItem class.
        :param port_name: The name of the port.
        :param ttl_seconds: Time interval to live in exclude list in seconds (0 - forever).
        """
        self.port_name = port_name
        self.ttl_seconds = ttl_seconds
        self.remove_time = 0 if ttl_seconds == 0 else time.time() + ttl_seconds


class ExcludeList:
    """
    Implements list for excluded ports.

    Attributes:
        __dict (dictionary): exclude ports dictionary.
        __logger: logger object
        __lock: synchronization object
    """

    def __init__(self, logger):
        """
        Initialize a new instance of the ExcludeList class.
        :param logger: Logger.
        """
        self.__logger = logger
        self.__dict = {}
        self.__lock = threading.RLock()


    def add(self, port_name, ttl_seconds = 0):
        """
        Add port to exclude list if not exist.
        If the port exists, its remove time will be updated.
        :param port_name: The name of the port.
        :param ttl_seconds: Time interval to live in exclude list in seconds (0 - forever).
        """
        with self.__lock:
            self.__dict[port_name] = ExcludeListItem(port_name, ttl_seconds)
            if ttl_seconds == 0:
                self.__logger.info(f"Port {port_name} is excluded forever")
            else:
                self.__logger.info(f"Port {port_name} is excluded for {ttl_seconds} seconds")


    def contains(self, port_name):
        """
        Check if port exists.
        Remove the port if its remove time is reached.
        :param port_name: The name of the port.
        :return: True if the port still exists, False otherwise.
        """
        with self.__lock:
            data = self.__dict.get(port_name)
            if data is not None:
                if data.remove_time == 0 or time.time() < data.remove_time:
                    # Excluded port
                    return True

                # The time is expired, so remove port from the list
                self.__dict.pop(port_name)
                self.__logger.info(f"Port {port_name} automatically removed from exclude list after {data.ttl_seconds} seconds")
        return False


    def remove(self, port_name):
        """
        Remove port from exclude list if exists.
        :param port_name: The name of the port.
        """
        with self.__lock:
            if port_name in self.__dict:
                self.__dict.pop(port_name)
                self.__logger.info(f"Port {port_name} removed from exclude list")
                return True
            return False


    def refresh(self):
        """
        Check all ports and remove the ports that its time to live in exclude list is expired.
        """
        with self.__lock:
            # Convert to list to avoid "dictionary changed size during iteration" error
            port_names = list(self.__dict.keys())
            for name in port_names:
                self.contains(name)


    def items(self):
        """
        Return all exclude list items.
        """
        self.refresh()
        with self.__lock:
            # Convert to list to avoid "dictionary changed size during iteration" error
            return list(self.__dict.values())
