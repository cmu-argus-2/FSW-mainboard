"""
Onboard Data Handling (OBDH) Module

======================

The OBDH module serves as the backbone of the satellite's data management system, providing a robust and efficient interface
for handling onboard persistent storage, inter-task communication, and telemetry.

This module provides the main interface for the onboard data handling system with the following features:
- Persistent storage management and single point of access for the onboard mass storage system (SD Card)
- Enables data retrieval and system state restoration across reboot cycles.
- Supports logging for flight software tasks with configurable intervals, storage limits, and buffering.
- Manages telemetry (TM) and telecommand (TC) file generation for transmission.
- Provides file exclusion, flagging, and deletion as an interface for the communication subsystem.
- File exclusion, flagging, and deletion as interface for a communication subsystem
- Handles binary encoding and decoding with configurable formats for efficient numerical and image data storage.
- Facilitates seamless data sharing and communication between flight software components.
- Binary encoding and decoding with configurable formats for compact and efficient storage of numerical and image data.
- Easily adaptable to diverse mission requirements.

Author: Ibrahima Sory Sow

Data format (character: byte size):
    "b": 1,  # byte
    "B": 1,  # unsigned byte
    "h": 2,  # short
    "H": 2,  # unsigned short
    "i": 4,  # int
    "I": 4,  # unsigned int
    "l": 4,  # long
    "L": 4,  # unsigned long
    "q": 8,  # long long
    "Q": 8,  # unsigned long long
    "f": 4,  # float
    "d": 8,  # double

"""

import json
import os
import re
import struct
import time

from core.logging import logger
from micropython import const

try:
    from typing import Any, List, Optional, Tuple
except ImportError:
    pass

_HOME_PATH = "/sd"  # Default path for the SD card
_CLOSED = const(20)
_OPEN = const(21)
_IMG_SIZE_LIMIT = const(100000)


_PROCESS_CONFIG_FILENAME = ".data_process_configuration.json"
_IMG_TAG_NAME = "img"


class DataProcess:
    """
    Class for managing a single logging stream.

    Attributes:
        tag_name (str): The tag name for the file.
        data_format (str): The format of the data to be written to the file.
        persistent (bool): Whether the data should be logged to a file (default is True).
        data_limit (int): The maximum number of data in bytes allowed in the file (default is 100kb).
                        This attribute will automatically get updated based on the line bytesize.
        new_config_file (bool): Whether to create a new configuration file (default is False).
        write_interval (int): The interval of logs at which the data should be written to the file (default is 1).
        write_interval_counter (int): The counter for the write interval.
        circular_buffer_size (int): The size of the circular buffer for the files in the directory (default is 10).
        retrieve_latest_data (bool): Whether to attempt to retrieve the latest data point and load it into the
                                    internal buffer (default is True).
        status (str): The status of the file ("CLOSED" or "OPEN").
        file (file): The file object.
        dir_path (str): The directory path for the file.
        current_path (str): The current filename.
        bytesize (int): The size of each new data line to be written to the file.
    """

    # For optimization purposes  (avoid creating a __dict__ and instantiate static memnory space for attributes)

    __slots__ = (
        "tag_name",
        "data_format",
        "persistent",
        "data_limit",
        "new_config_file",
        "write_interval",
        "write_interval_counter",
        "circular_buffer_size",
        "retrieve_latest_data",
        "append_to_current",
        "status",
        "file",
        "dir_path",
        "current_path",
        "bytesize",
        "size_limit",
        "last_data",
        "delete_paths",
        "excluded_paths",
    )

    _FORMAT = {
        "b": 1,  # byte
        "B": 1,  # unsigned byte
        "h": 2,  # short
        "H": 2,  # unsigned short
        "i": 4,  # int
        "I": 4,  # unsigned int
        "l": 4,  # long
        "L": 4,  # unsigned long
        "q": 8,  # long long
        "Q": 8,  # unsigned long long
        "f": 4,  # float
        "d": 8,  # double
    }

    def __init__(
        self,
        tag_name: str,
        data_format: str,
        persistent: bool = True,
        data_limit: int = 100000,
        write_interval: int = 1,
        circular_buffer_size: int = 10,
        retrieve_latest_data: bool = True,
        append_to_current: bool = True,
        new_config_file: bool = False,
    ) -> None:
        """
        Initializes a DataProcess object.

        Args:
            tag_name (str): The tag name for the file (with no spaces or special characters).
            data_format (str): The format of the data to be written to the file. e.g. 'iff', 'iif', 'fff', 'iii', etc.
            persistent (bool, optional): Whether the file should be persistent or not (default is True).
            data_limit (int, optional): The maximum number of data in bytes allowed in the file (default is 100kb).
                                        This attribute will automatically get updated based on the line bytesize.
            circular_buffer_size (int, optional): The size of the circular buffer for the files in
                                        the directory (default is 10).
            retrieve_latest_data (bool, optional): Whether to attempt to retrieve the latest data point (default is True)
                                        and load it into the internal buffer.
            append_to_current (bool, optional): Whether to attempt to append to the current file (default is True) instead
                                                of creating a new file.
            new_config_file (bool, optional): Whether to create a new configuration file (default is False).
        """

        self.tag_name = tag_name
        self.file = None
        self.persistent = persistent
        self.write_interval = int(write_interval)
        self.write_interval_counter = self.write_interval - 1  # To write the first data point
        self.circular_buffer_size = circular_buffer_size
        self.retrieve_latest_data = retrieve_latest_data
        self.append_to_current = append_to_current

        self.current_path = None

        # TODO Check formating e.g. 'iff', 'iif', 'fff', 'iii', etc. ~ done within compute_bytesize()
        self.data_format = "<" + data_format
        # Need to specify endianness to disable padding
        # (https://stackoverflow.com/questions/47750056/python-struct-unpack-length-error/47750278#47750278)
        self.bytesize = self.compute_bytesize(self.data_format)

        self.last_data = None

        self.delete_paths = []  # Paths that are flagged for deletion
        self.excluded_paths = []  # Paths that are currently being transmitted

        if self.persistent:
            self.status = _CLOSED

            self.dir_path = join_path(_HOME_PATH, tag_name)
            self.create_folder()

            # To Be Resolved for each file process, TODO check if int, positive, etc
            self.size_limit = (
                data_limit // self.bytesize
            )  # + (data_limit % self.bytesize)   # Default size limit is 1000 data lines

            if retrieve_latest_data:
                # attempt to retrieve the latest data point and load it into the internal buffer
                self.retrieve_last_data_from_latest_file()

            self.initialize_current_file()

            config_file_path = join_path(self.dir_path, _PROCESS_CONFIG_FILENAME)
            if not path_exist(config_file_path) or new_config_file:
                config_data = {
                    "data_format": self.data_format[1:],  # remove the < character
                    "data_limit": data_limit,
                    "write_interval": write_interval,
                    "retrieve_latest_data": retrieve_latest_data,
                    "append_to_current": append_to_current,
                }
                with open(config_file_path, "w") as config_file:
                    json.dump(config_data, config_file)

    def create_folder(self) -> None:
        """
        Creates a folder for the file if it doesn't already exist.
        """
        if not path_exist(self.dir_path):
            try:
                os.mkdir(self.dir_path)
                logger.info(f"Folder {self.dir_path} created successfully.")
            except OSError as e:
                logger.critical(f"Error creating folder: {e}")
        else:
            logger.info("Folder already exists.")

    @classmethod
    def compute_bytesize(cls, data_format: str) -> int:
        """
        Compute the bytesize for each new data line to be written to the file.

        Args:
            data_format (str): The format of the data.

        Returns:
            int: The bytesize of each new data line.
        """
        b_size = 0
        for c in data_format[1:]:  # do not include the endianness character
            if c not in cls._FORMAT:
                raise ValueError(f"Invalid format character '{c}'")
            b_size += cls._FORMAT[c]
        return b_size

    def log(self, data: List) -> None:
        """
        Logs the given data (eventually also to a file if persistent = True).

        Args:
            data (List): The data to be logged.

        Returns:
            None
        """

        self.last_data = data

        if self.persistent:
            self.resolve_current_file()
            self.write_interval_counter += 1

            if self.write_interval_counter >= self.write_interval:
                bin_data = struct.pack(self.data_format, *data)
                self.file.write(bin_data)
                self.file.flush()  # Flush immediately
                self.write_interval_counter = 0

    def get_latest_data(self) -> Optional[List]:
        """
        Returns the latest data point.

        If a data point has been logged, it returns the last data point.
        If no data point has been logged yet, it returns None.

        Returns:
            The latest data point or None if no data point is available yet.
        """
        if self.last_data is not None:
            return self.last_data
        else:
            logger.warning("No latest data point available.")
            return None

    def clear_latest_data(self) -> bool:
        """
        Clears the latest data point.
        """
        self.last_data = None

    def data_available(self) -> bool:
        """
        Returns whether data is available in the internal buffer (latest).
        If data is  not available, it is either because nothing has been logged yet
        or the data has been cleared.
        """
        return self.last_data is not None

    def resolve_current_file(self) -> None:
        """
        Resolve the current file to write to.
        """
        if self.status == _CLOSED:
            self.current_path = self.create_new_path()
            self.open()
        elif self.status == _OPEN:
            current_file_size = self.get_current_file_size()
            if current_file_size >= self.size_limit:
                self.close()
                self.current_path = self.create_new_path()
                self.open()

    def create_new_path(self) -> str:
        """
        Create a new filename for the current file process.

        Returns:
            str: The new filename.
        """
        # Keeping the tag name in the filename for identification in debugging
        return join_path(self.dir_path, self.tag_name) + "_" + str(int(time.time())) + ".bin"

    def try_to_reuse_latest_file(self) -> bool:
        """
        Attempt to reuse the latest file in the directory.
        Returns True if the file was successfully reused, False otherwise.
        """
        latest_file = self._get_latest_file()
        if latest_file is not None:
            try:
                self.current_path = latest_file
                self.open()
                return True
            except Exception as e:
                logger.error(f"Error reusing latest file {latest_file}: {e}")
                return False
        else:
            return False

    def initialize_current_file(self) -> None:
        """
        Initialize the current file path, either by reusing the latest file or creating a new one.
        """
        if not self.append_to_current or not self.try_to_reuse_latest_file():
            self.current_path = self.create_new_path()
        # else: # for debugging
        #    print("Reusing latest file ", self.current_path)

    def retrieve_last_data_from_latest_file(self) -> bool:
        """
        Retrieve the last data point from the latest file in the directory.
        Returns True if the data was successfully retrieved, False otherwise.
        """
        latest_file = self._get_latest_file()
        if latest_file is not None:
            try:
                with open(latest_file, "rb") as file:
                    SEEK_END = 2
                    file.seek(-self.bytesize, SEEK_END)  # SEEK_END == 2
                    cr = file.read(self.bytesize)
                    if len(cr) != self.bytesize:  # Handle incomplete data
                        return False
                    self.last_data = struct.unpack(self.data_format, cr)
                    return True
            except Exception as e:
                logger.warning(f"Error reading file {latest_file}: {e}")
                # might want to delete the file in case of corruption if we don't have mechanism to "repair" it
                return False
        else:
            return False

    def open(self) -> None:
        """
        Open the file for writing.
        """
        if self.status == _CLOSED:
            self.file = open(self.current_path, "ab+")
            self.status = _OPEN
        else:
            logger.info("File is already open.")

    def close(self) -> None:
        """
        Close the file.
        """
        if self.status == _OPEN:
            self.file.close()
            self.status = _CLOSED
        else:
            logger.info("File is already closed.")

    def _get_latest_file(self) -> Optional[str]:
        """
        Helper functions that returns the path of the latest file in the directory if it exists.
        If no file is available, the function returns None.
        """
        files = self.get_sorted_file_list()
        if len(files) > 1:  # Ignore process configuration file
            file = files[-1]
            if file == _PROCESS_CONFIG_FILENAME:
                file = files[-2]
            path = join_path(self.dir_path, file)
            return path
        else:
            return None

    def request_TM_path(self, latest: bool = False, file_time=None) -> Optional[str]:
        """
        Returns the path of a designated file available for transmission.
        If no file is available, the function returns None.

        The function store the file path to be excluded in a separate list.
        Once fully transmitted, notify_TM_path() must be called to remove the file from the exclusion list
        and prepare for deletion.
        """
        files = self.get_sorted_file_list()
        if len(files) > 1:  # Ignore process configuration file
            if latest or (
                file_time is not None and file_time == 0
            ):  # Edge case for when time = 0 we want to return the latest
                transmit_file = files[-1]
                if transmit_file == _PROCESS_CONFIG_FILENAME:
                    transmit_file = files[-2]
            else:
                transmit_file = files[0]
                if transmit_file == _PROCESS_CONFIG_FILENAME:
                    transmit_file = files[1]

                if file_time is not None:
                    result_file = get_closest_file_time(file_time, files)
                    transmit_file = result_file if result_file is not None else transmit_file

            tm_path = join_path(self.dir_path, transmit_file)

            if tm_path == self.current_path:
                self.close()
                self.resolve_current_file()

            self.excluded_paths.append(tm_path)
            return tm_path
        else:
            return None

    def notify_TM_path(self, path: str) -> None:
        """
        Acknowledge the transmission of the file.
        The file is then removed from the excluded list and added to the deletion list.
        """
        if path in self.excluded_paths:
            self.excluded_paths.remove(path)
            self.delete_paths.append(path)
            # TODO handle case where comms transmitted a file it wasn't suposed to
        else:
            logger.info("No file to acknowledge.")

    def clean_up(self) -> None:
        """
        Clean up the files that have been marked for deletion.
        """
        for d_path in self.delete_paths[:]:  # IMPORTANT: Iterate over a COPY of the list
            # shouldn't iterate over the same list we're removing from
            if path_exist(d_path):
                os.remove(d_path)
            else:
                # TODO - log error, use exception handling instead
                logger.critical(f"File {d_path} does not exist.")
            self.delete_paths.remove(d_path)

    def check_circular_buffer(self) -> None:
        """
        Checks the circular buffer for the number of files and manages the deletion of the oldest files if necessary.

        This method performs the following steps:
        1. Retrieves the list of files in the directory, excluding the process configuration file.
        2. Compares the number of files against the circular buffer size, adjusted for excluded and delete paths.
        3. If the number of files exceeds the circular buffer size, it marks the oldest file for deletion,
           ignoring files in excluded_paths and delete_paths.

        Note:
            - The method updates the delete_paths list with the files marked for deletion.
            - The actual deletion of files is not performed by this method.

        Returns:
            None
        """
        files = self.get_sorted_file_list()[1:]  # Ignore process configuration file
        # Actual overflow of the buffer
        diff = len(files) - (self.circular_buffer_size + len(self.excluded_paths) + len(self.delete_paths) - 1)
        # -1 for the current file
        mark_counter = 0
        if diff > 0:
            # diff files to mark for deletion
            for file in files:
                file = join_path(self.dir_path, file)
                if file not in self.excluded_paths and file not in self.delete_paths and file != self.current_path:
                    self.delete_paths.append(file)  # mark for deletion
                    mark_counter += 1
                if mark_counter == diff:
                    break

    def get_sorted_file_list(self) -> List[str]:
        """
        Returns a list of all files in the directory.

        Returns:
            A list of filenames.
        """
        return sorted(os.listdir(self.dir_path))

    def get_storage_info(self) -> Tuple[int, int]:
        """
        Returns storage information for the current file process which includes:
        - Number of files in the directory
        - Total directory size in bytes
        - TODO

        Returns:
            A tuple containing the number of files and the total directory size.
        """
        files = os.listdir(self.dir_path)
        # TODO - implement the rest of the function
        total_size = (len(files) - 2) * self.size_limit + self.get_current_file_size()
        return (len(files) - 1), total_size

    def get_current_file_size(self) -> Optional[int]:
        """
        Get the current size of the file.

        Returns:
            Optional[int]: The size of the file in bytes, or None if there was an error or the file does not exist.
        """
        if path_exist(self.current_path):
            try:
                file_stats = os.stat(self.current_path)
                filesize = file_stats[6]  # size of the file in bytes
                return filesize
            except OSError as e:
                logger.error(f"Error getting file size: {e}")
                return None
        else:
            # TODO handle case where file does not exist
            logger.warning(f"File {self.current_path} does not exist.")
            return None

    # DEBUG ONLY
    def read_current_file(self) -> List[Tuple[Any, ...]]:
        """
        Reads the content of the current file.

        Returns:
            A list of tuples representing the content of the file.
            Each tuple contains the unpacked data from a line in the file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        self.close()
        if self.status == _CLOSED:
            # TODO file not existing
            with open(self.current_path, "rb") as file:
                content = []
                # TODO add max iter (max lines to read from file)
                while True:
                    cr = file.read(self.bytesize)
                    if not cr:
                        break
                    content.append(struct.unpack(self.data_format, cr))
                return content
        else:
            logger.warning(f"Can't read {self.current_path}: File is not closed!")


class ImageProcess(DataProcess):
    def __init__(self, tag_name: str):
        self.tag_name = tag_name
        self.file = None

        self.status = _CLOSED

        self.dir_path = join_path(_HOME_PATH, self.tag_name)
        self.create_folder()

        self.size_limit = _IMG_SIZE_LIMIT

        self.current_path = self.create_new_path()
        self.delete_paths = []  # Paths that are flagged for deletion
        self.excluded_paths = []  # Paths that are currently being transmitted
        self.circular_buffer_size = 20  # Default size of the circular buffer for the files in the directory

        config_file_path = join_path(self.dir_path, _PROCESS_CONFIG_FILENAME)
        if not path_exist(config_file_path):
            config_data = {_IMG_TAG_NAME: True}
            with open(config_file_path, "w") as config_file:
                json.dump(config_data, config_file)

    def resolve_current_file(self) -> None:
        """
        Resolve the current image to write to.
        """
        if self.status == _CLOSED:
            self.current_path = self.create_new_path()
            self.open()
        elif self.status == _OPEN:
            current_file_size = self.get_current_file_size()
            if current_file_size >= self.size_limit:
                self.close()
                self.current_path = self.create_new_path()
                self.open()

    def create_new_path(self) -> str:
        """
        Create a new filename for the image process.

        Returns:
            str: The new filename.
        """
        # Keeping the tag name in the filename for identification
        return join_path(self.dir_path, self.tag_name) + "_" + str(int(time.time())) + ".jpg"

    def log(self, data: bytearray) -> None:
        """
        Logs the given image data.

        Args:
            data (List[bytes]): The bytes of image data to be logged.

        Returns:
            None
        """
        self.resolve_current_file()
        self.last_data = data

        self.file.write(data)
        self.file.flush()

    def request_TM_path(self, latest: bool = False, file_time=None) -> Optional[str]:
        """
        MODIFIED FOR IMAGES as we need complete images to be transmitted.

        Returns the path of a designated image available for transmission.
        If no image is available, the function returns None.

        The function store the file path to be excluded in a separate list.
        Once fully transmitted, notify_TM_path() must be called to remove the file from the exclusion list
        and prepare for deletion.
        """
        files = self.get_sorted_file_list()
        if len(files) > 1:  # Ignore process configuration file
            if latest:
                transmit_file = files[-1]
                if transmit_file == _PROCESS_CONFIG_FILENAME:
                    transmit_file = files[-2]
            else:
                transmit_file = files[0]
                if transmit_file == _PROCESS_CONFIG_FILENAME:
                    transmit_file = files[1]

                if file_time is not None:
                    result_file = get_closest_file_time(file_time, files)
                    transmit_file = result_file if result_file is not None else transmit_file

            tm_path = join_path(self.dir_path, transmit_file)

            if tm_path == self.current_path or not path_exist(tm_path):
                return None

            self.excluded_paths.append(tm_path)
            return tm_path
        else:
            return None

    def image_completed(self):
        """
        Closes the current file and resolves it, to prepare for the next image.

        Returns:
            None
        """
        self.close()
        self.resolve_current_file()


class DataHandler:
    """
    Managing class for all data processes and the SD card.

    Note: If the same SPI bus is shared with other peripherals, the SD card must be initialized
    before accessing any other peripheral on the bus.
    Failure to do so can prevent the SD card from being recognized until it is powered off or re-inserted.
    """

    _SD_SCANNED = False
    _SD_USAGE = 0
    SD_ERROR_FLAG = False

    # Keep track of all file processes
    data_process_registry = dict()

    @classmethod
    def scan_SD_card(cls) -> None:
        """
        Scans the SD card for configuration files and registers data processes.

        This method scans the SD card for directories and checks if each directory contains a configuration file.
        If a configuration file is found, it reads the data format and line limit from the file and registers
        a data process with the specified parameters.

        If an 'img' configuration is found, it registers an image process with the specified data format.

        Returns:
            None

        Example:
            DataHandler.scan_SD_card()
        """
        if not path_exist(_HOME_PATH):
            # The SD card path has an issue
            cls.SD_ERROR_FLAG = True
        else:
            cls.SD_ERROR_FLAG = False
            directories = cls.list_directories()
            for dir_name in directories:
                config_file = join_path(_HOME_PATH, dir_name, _PROCESS_CONFIG_FILENAME)
                if path_exist(config_file):
                    with open(config_file, "r") as f:
                        config_data = json.load(f)

                        if _IMG_TAG_NAME in config_data:
                            data_format: str = config_data.get(_IMG_TAG_NAME)
                            cls.register_image_process()
                            continue
                        data_format: str = config_data.get("data_format")
                        data_limit: int = config_data.get("data_limit")
                        write_interval: int = config_data.get("write_interval")
                        retrieve_latest_data: bool = config_data.get("retrieve_latest_data")
                        append_to_current: bool = config_data.get("append_to_current")
                        if data_format and data_limit:
                            cls.register_data_process(
                                tag_name=dir_name,
                                data_format=data_format,
                                persistent=True,
                                data_limit=data_limit,
                                write_interval=write_interval,
                                retrieve_latest_data=retrieve_latest_data,
                                append_to_current=append_to_current,
                            )
        cls._SD_SCANNED = (
            True  # Need this flag to be set to True for the rest to proceed, irrespective of an SD card failure or not
        )

    @classmethod
    def SD_SCANNED(cls) -> bool:
        """
        Returns the status of the SD card scanning.

        Returns:
            bool: True if the SD card has been scanned, False otherwise.
        """
        return cls._SD_SCANNED

    @classmethod
    def register_data_process(
        cls,
        tag_name: str,
        data_format: str,
        persistent: bool,
        data_limit: int = 100000,
        write_interval: int = 1,
        circular_buffer_size: int = 10,
        retrieve_latest_data: bool = True,
        append_to_current: bool = True,
    ) -> None:
        """
        Register a data process with the given parameters.

        Parameters:
        - tag_name (str): The name of the data process.
        - data_format (str): The format of the data.
        - persistent (bool): Whether the data should be logged to a file.
        - data_limit (int, optional): The maximum number of data lines to store. Defaults to 100000 bytes.
        - write_interval (int, optional): The interval of logs at which the data should be written to the file. Defaults to 1.
        - circular_buffer_size (int, optional): The size of the circular buffer for the files in the directory. Defaults to 10.
        - retrieve_latest_data (bool, optional): Whether to attempt to retrieve the latest data point and load it into the
        internal buffer. Defaults to True.
        - append_to_current (bool, optional): Whether to attempt to append to the current file instead of creating a new file.
        Defaults to True.

        Raises:
        - ValueError: If data_limit is not a positive integer.

        Returns:
        - None
        """
        if isinstance(data_limit, int) and data_limit > 0:
            cls.data_process_registry[tag_name] = DataProcess(
                tag_name,
                data_format,
                persistent=persistent if cls.SD_ERROR_FLAG is False else False,
                data_limit=data_limit,
                write_interval=write_interval,
                circular_buffer_size=circular_buffer_size,
                retrieve_latest_data=retrieve_latest_data,
                append_to_current=append_to_current,
            )
            if cls.SD_ERROR_FLAG:
                logger.warning(f"Data process {tag_name} not persistent due to SD card error.")
        else:
            raise ValueError("Data limit must be a positive integer.")

    @classmethod
    def register_image_process(cls) -> None:
        """
        Register an image process with the given data format.

        Returns:
        - None
        """
        cls.data_process_registry[_IMG_TAG_NAME] = ImageProcess(_IMG_TAG_NAME)

    @classmethod
    def log_data(cls, tag_name: str, data: List) -> None:
        """
        Logs the provided data using the specified tag name.

        Parameters:
        - tag_name (str): The name of data process to associate with the logged data.
        - data (List): The data to be logged.

        Raises:
        - KeyError: If the provided tag name is not registered in the data process registry.

        Returns:
        - None
        """
        try:
            if tag_name in cls.data_process_registry:
                cls.data_process_registry[tag_name].log(data)
            else:
                raise KeyError("Data process not registered!")
        except KeyError as e:
            logger.critical(f"Error: {e}")

    @classmethod
    def log_image(cls, data: List[bytes]) -> None:
        """
        Logs the provided image data.

        Parameters:
        - data (List[bytes]): The image data to be logged.

        Returns:
        - None
        """
        try:
            if _IMG_TAG_NAME in cls.data_process_registry:
                cls.data_process_registry[_IMG_TAG_NAME].log(data)
            else:
                raise KeyError("Data process not registered!")
        except KeyError as e:
            logger.critical(f"Error: {e}")

    @classmethod
    def image_completed(cls) -> bool:
        """
        Closes the current file and resolves it, to prepare for the next image.

        Returns:
            None
        """
        try:
            if _IMG_TAG_NAME in cls.data_process_registry:
                cls.data_process_registry[_IMG_TAG_NAME].image_completed()
            else:
                raise KeyError("Image data process not registered!")
        except KeyError as e:
            logger.critical(f"Error: {e}")

    @classmethod
    def get_latest_data(cls, tag_name: str):
        """
        Returns the latest data point for the specified data process.

        Parameters:
        - tag_name (str): The name of the data process.

        Returns:
        - The latest data point for the specified data process or None if the data process does not exist.
        """
        if cls._check_tag_name(tag_name):
            return cls.data_process_registry[tag_name].get_latest_data()
        else:
            return None

    @classmethod
    def clear_latest_data(cls, tag_name: str) -> bool:
        """
        Clears the latest data point for the specified data process.

        Parameters:
        - tag_name (str): The name of the data process.

        Returns True if the latest data point was cleared, False otherwise
        (and if a tag_name associated to a data process does not exist).
        """
        if cls._check_tag_name(tag_name):
            return cls.data_process_registry[tag_name].clear_latest_data()
        else:
            return False

    @classmethod
    def data_available(cls, tag_name: str) -> bool:
        """
        Returns whether data is available in the internal buffer (latest) for the specified data process.
        If data is not available, it is either because nothing has been logged yet or the data has been cleared.

        Parameters:
        - tag_name (str): The name of the data process.

        Returns:
        - bool: True if data is available, False otherwise (and if a tag_name associated to a data process does not exist).
        """
        if cls._check_tag_name(tag_name):
            return cls.data_process_registry[tag_name].data_available()
        else:
            return False

    @classmethod
    def check_SD_status(cls) -> bool:
        """
        Returns the status of the SD card.

        Returns:
        - bool: True if the SD card is functioning correctly, False otherwise.
        """
        return not cls.SD_ERROR_FLAG

    @classmethod
    def list_directories(cls) -> List[str]:
        """
        Returns a list of directories in the SD card path.

        Returns:
            A list of directory names.

        Example:
            directories = DataHandler.list_directories()
        """
        return os.listdir(_HOME_PATH)

    # DEBUG ONLY
    @classmethod
    def get_data_process(cls, tag_name: str) -> DataProcess:
        """
        Returns the data process object associated with the specified tag name.

        Parameters:
            tag_name (str): The name of the data process.

        Raises:
            KeyError: If the provided tag name is not registered in the data process registry.

        Returns:
            The data process object.

        Example:
            process = DataHandler.get_data_process('tag_name')
        """
        return cls.data_process_registry[tag_name]

    @classmethod
    def get_all_data_processes_name(cls) -> List[str]:
        """
        Returns a list of all registered data process names.

        Returns:
            A list of data process names.

        Example:
            names = DataHandler.get_all_data_processes_name()
        """
        return list(cls.data_process_registry.keys())

    # DEBUG ONLY
    @classmethod
    def get_all_data_processes(cls) -> List[DataProcess]:
        """
        Returns a list of all registered data process objects.

        Returns:
            A list of data process objects.

        Example:
            processes = DataHandler.get_all_data_processes()
        """
        return list(cls.data_process_registry.values())

    @classmethod
    def get_storage_info(cls, tag_name: str):
        """
        Prints the storage information for the specified data process.

        Parameters:
            tag_name (str): The name of the data process.

        Raises:
            KeyError: If the provided tag name is not registered in the data process registry.

        Returns:
            Tuple containing storage information for the tag name if it exists

        Example:
            DataHandler.get_storage_info('tag_name')
        """
        try:
            if tag_name in cls.data_process_registry:
                return cls.data_process_registry[tag_name].get_storage_info()
            else:
                raise KeyError("File process not registered.")
        except KeyError as e:
            logger.warning(f"Error: {e}")

    @classmethod
    def data_process_exists(cls, tag_name: str) -> bool:
        """
        Check if a data process with the specified tag name exists.

        Parameters:
            tag_name (str): The name of the data process.

        Returns:
            bool: True if the data process exists, False otherwise.
        """
        return tag_name in cls.data_process_registry

    @classmethod
    def image_process_exists(cls) -> bool:
        """
        Check if the image process exists.

        Returns:
            bool: True if the image process exists, False otherwise.
        """
        return _IMG_TAG_NAME in cls.data_process_registry

    @classmethod
    def request_TM_path(cls, tag_name, latest=False, file_time=None):
        """
        Returns the path of a designated file available for transmission.
        If no file is available, the function returns None.

        The function store the file path to be excluded in a separate list.
        Once fully transmitted, notify_TM_path() must be called to remove the file from the exclusion list
        and prepare for deletion.
        """
        try:
            if tag_name in cls.data_process_registry:
                return cls.data_process_registry[tag_name].request_TM_path(latest=latest, file_time=file_time)
            else:
                raise KeyError("Data  process not registered!")
        except KeyError as e:
            logger.critical(f"Error: {e}")

    @classmethod
    def request_TM_path_image(cls, latest=False, file_time=None):
        """
        Returns the path of a designated image available for transmission.
        If no file is available, the function returns None.

        The function store the file path to be excluded in a separate list.
        Once fully transmitted, notify_TM_path() must be called to remove the file from the exclusion list
        and prepare for deletion.
        """
        try:
            if "img" in cls.data_process_registry:
                return cls.data_process_registry["img"].request_TM_path(latest=latest, file_time=file_time)
            else:
                raise KeyError("Image process not registered!")
        except KeyError as e:
            logger.critical(f"Error: {e}")

    @classmethod
    def notify_TM_path(cls, tag_name, path):
        """
        Acknowledge the transmission of the file.
        The file is then removed from the exclusion list.
        """
        try:
            if tag_name in cls.data_process_registry:
                cls.data_process_registry[tag_name].notify_TM_path(path)
            else:
                raise KeyError("Data process not registered!")
        except KeyError as e:
            logger.critical(f"Error: {e}")

    @classmethod
    def clean_up(cls):
        """
        Clean up the files that have been transmitted and acknowledged.
        """
        for tag_name in cls.data_process_registry:
            cls.data_process_registry[tag_name].clean_up()

    @classmethod
    def check_circular_buffers(cls):
        """
        Check the circular buffers for each data process and mark for deletion the oldest files if necessary
        while taking into account the existing paths that are excluded or already marked for deletion.
        """
        for tag_name in cls.data_process_registry:
            cls.data_process_registry[tag_name].check_circular_buffer()

    @classmethod
    def delete_all_files(cls, path=None):
        if path is None:
            path = _HOME_PATH
        try:
            for file_name in os.listdir(path):
                file_path = join_path(path, file_name)
                if os.stat(file_path)[0] & 0x8000:  # Check if file is a regular file
                    os.remove(file_path)
                elif os.stat(file_path)[0] & 0x4000:  # Check if file is a directory
                    cls.delete_all_files(file_path)  # Recursively delete files in subdirectories
                    os.rmdir(file_path)  # Delete the empty directory
            logger.info("All files and directories deleted successfully!")
        except Exception as e:
            logger.warning(f"Error deleting files and directories: {e}")

    @classmethod
    def get_current_file_size(cls, tag_name):
        try:
            if tag_name in cls.data_process_registry:
                return cls.data_process_registry[tag_name].get_current_file_size()
            else:
                raise KeyError("File process not registered!")
        except KeyError as e:
            logger.warning(f"Error: {e}")

    @classmethod
    def compute_total_size_files(cls, root_path: str = None) -> int:
        """
        Computes the total size of all files under the sd_path.

        Returns:
        - The total size in bytes.
        """
        # TODO Remove recursion, really bad
        if root_path is None:
            root_path = _HOME_PATH
        total_size: int = 0
        for entry in os.listdir(root_path):
            file_path: str = join_path(root_path, entry)
            if os.stat(file_path)[0] & 0x4000:  # Check if entry is a directory
                total_size += cls.compute_total_size_files(
                    file_path
                )  # Recursively compute total size of files in subdirectories
            else:
                total_size += os.stat(file_path)[6]
            pass
        return int(total_size)

    @classmethod
    def update_SD_usage(cls) -> None:
        cls._SD_USAGE = cls.compute_total_size_files()

    @classmethod
    def SD_usage(cls) -> int:
        return cls._SD_USAGE

    # DEBUG ONLY
    @classmethod
    def print_directory(cls, path: str = None, tabs: int = 0) -> None:
        """
        Prints the directory contents recursively.

        Parameters:
            path (str, optional): The path of the directory. Defaults to "/sd".
            tabs (int, optional): The number of tabs for indentation. Defaults to 0.

        Returns:
            None
        """
        if path is None:
            path = _HOME_PATH
        for file in os.listdir(path):
            stats = os.stat(join_path(path, file))
            filesize = stats[6]
            isdir = stats[0] & 0x4000
            if filesize < 1000:
                sizestr = str(filesize) + " by"
            elif filesize < 1000000:
                sizestr = "%0.1f KB" % (filesize / 1000)
            else:
                sizestr = "%0.1f MB" % (filesize / 1000000)
            printname = ""
            for _ in range(tabs):
                printname += "   "
            printname += file
            if isdir:
                printname += "/"
            print("{0:<40} Size: {1:>10}".format(printname, sizestr))
            # recursively print directory contents
            if isdir:
                cls.print_directory(join_path(path, file), tabs + 1)

    @classmethod
    def _check_tag_name(cls, tag_name: str) -> bool:
        """
        Checks if the tag name is valid.
        """
        if tag_name in cls.data_process_registry:
            return True
        else:
            logger.critical("Data process '{}' not registered!".format(tag_name))
            return False


def path_exist(path: str) -> bool:
    """
    Replacement for os.path.exists() function, which is not implemented in micropython.
    If the request for a directory, the function will return True if the directory exists,
    even if it is empty.
    """
    try_path = path
    if path[-1] == "/":
        try_path = path[:-1]

    try:
        os.stat(try_path)
        return True
    except OSError as e:
        logger.info(f"{e} - {try_path} doesn't exist")
        return False


def join_path(*paths: str) -> str:
    """
    Join multiple paths together into a single path.

    Args:
        *paths: Variable number of paths to be joined.

    Returns:
        The joined path.
    """
    if not paths:
        return ""

    joined_path = "/".join(paths)
    normalized_path = re.sub(r"/+", "/", joined_path)  # remove multiple slashes
    # Remove leading slash if this was not an absolute path
    if not paths[0].startswith("/"):
        normalized_path = normalized_path.lstrip("/")
    return normalized_path


def extract_time_from_filename(filename: str) -> int:
    """
    Extracts the timestamp from a filename formatted as 'TAGNAME_TIME.bin' or 'img_TIME.jpg'.

    Args:
        filename (str): The filename to extract the timestamp from.

    Returns:
        int: The timestamp extracted from the filename.
    """
    if not filename:
        return None

    if filename[-4:] == ".bin" or filename[-4:] == ".jpg":
        filename = filename[:-4]
    else:
        logger.warning(f"Invalid filename format for {filename}")
        return None

    match = re.search(r"_(\d+)", filename)
    if match:
        return int(match.group(1))
    else:
        logger.warning(f"Invalid filename format for {filename}")
        return None


def get_closest_file_time(file_time: int, files: List[str]):
    """
    Search through all the files to find the file name with the closest file time requested.
    Used for requesting file paths

    Args:
        file_time(int): The requested file time
        files(List[str]): A List of all the files for that data process

    Returns:
        str: file path with the closest file time to the one requested
    """
    # Search for the specific file with closest time to requested file time
    try:
        return min(files, key=lambda f: abs(extract_time_from_filename(f) - file_time))
    except TypeError as e:
        logger.warning(f"Could not find closest file time: {e}")
        return None
