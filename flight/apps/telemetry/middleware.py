"""
This is the file that will sit in between the comms tasks and Splat
it will have functions to encode and decode telemetry packets
    gathering the variables and all of that
"""

import gc

try:
    from micropython import const
except ImportError:
    # Fallback for testing on regular Python
    def const(x):
        return x


from apps.telemetry.splat.splat.telemetry_codec import Report
from core import DataHandler as DH
from core import logger
from core.dh_constants import ADCS_IDX, CDH_IDX, EPS_IDX, GPS_IDX, STORAGE_IDX


class Frame:
    """
    Representation of a frame of telemetry data. Replacing the old telemetry packer

    maybe will use this for more than telemetry later on
    """

    @classmethod
    def get_dh_latest_data(cls, ss):
        """
        Given a subsystem (string) it will grab the latest data from DH
        and return it
        """

        if not DH.data_process_exists(ss):
            # requested subsystem does not exist in DH
            logger.warning(f"No {ss.upper()} data process exists")
            return None

        data = DH.get_latest_data(ss)
        if data is None:
            logger.warning(f"No latest {ss.upper()} data available")
            return None

        return data

    @classmethod
    def get_storage_info(cls, ss):
        """
        Given a subsystem (string) it will grab the storage info from DH
        and return it
        will return a tuple (numebr_of_files, dir_size (bytes))
        """

        if not DH.data_process_exists(ss):
            # requested subsystem does not exist in DH
            logger.warning(f"No {ss.upper()} storage process exists")
            return None

        data = DH.get_storage_info(ss)
        if data is None:
            logger.warning(f"No {ss.upper()} storage info available")
            return None

        return data

    @classmethod
    def pack_tm_heartbeat(cls):
        """
        Pack a heartbeat telemetry frame.
        """
        # this will be a report
        report = Report("TM_HEARTBEAT")

        ss_list = ["cdh", "eps", "adcs", "gps"]  # we need this to get the from dh, and it is case sensitive
        idx_list = [CDH_IDX, EPS_IDX, ADCS_IDX, GPS_IDX]  # this is used to match the ss to the dh constants
        # get the latest data from each subsystem
        dh_data_list = [cls.get_dh_latest_data(x) for x in ss_list]

        # for each variable in the report, get the corresponding data from DH
        for ss in report.variables.keys():
            ss_lower = ss.lower()  # Create lowercase version for lookups
            if ss_lower not in ss_list:
                logger.warning(f"Subsystem {ss.upper()} not recognized for heartbeat")
                continue

            dh_data = dh_data_list[ss_list.index(ss_lower)]
            if dh_data is None:
                logger.warning(f"No data for subsystem {ss.upper()} to pack in heartbeat")
                continue

            # iterating over all the variables for the ss in the report and adding them
            for var_name in report.variables[ss].keys():
                dh_var_idx = getattr(idx_list[ss_list.index(ss_lower)], var_name)
                report.add_variable(var_name, ss, dh_data[dh_var_idx])

        logger.debug(f"Packed heartbeat telemetry frame {report}")

        gc.collect()

        return report

    @classmethod
    def pack_tm_hal(cls):
        """
        Pack a HAL telemetry frame.
        """
        # this will be a report
        report = Report("TM_HAL")

        ss_list = ["cdh", "eps", "storage"]  # we need this to get the from dh, and it is case sensitive
        idx_list = [CDH_IDX, EPS_IDX, STORAGE_IDX]  # this is used to match the ss to the dh constants
        # get the latest data from each subsystem
        dh_data_list = [cls.get_dh_latest_data(x) for x in ss_list]

        # for each variable in the report, get the corresponding data from DH
        for ss in report.variables.keys():
            ss_lower = ss.lower()  # Create lowercase version for lookups
            if ss_lower not in ss_list:
                logger.warning(f"Subsystem {ss.upper()} not recognized for HAL")
                continue

            dh_data = dh_data_list[ss_list.index(ss_lower)]
            if dh_data is None:
                logger.warning(f"No data for subsystem {ss.upper()} to pack in HAL")
                continue

            # iterating over all the variables for the ss in the report and adding them
            for var_name in report.variables[ss].keys():
                dh_var_idx = getattr(idx_list[ss_list.index(ss_lower)], var_name)
                report.add_variable(var_name, ss, dh_data[dh_var_idx])

        logger.debug(f"Packed HAL telemetry frame {report}")

        gc.collect()

        return report

    @classmethod
    def pack_tm_storage(cls):
        """
        Pack a storage telemetry frame.
        """
        # this will be a report
        report = Report("TM_STORAGE")

        ss_list = ["cdh"]  # we need this to get the from dh, and it is case sensitive
        storage_ss_list = [
            "cdh",
            "eps",
            "adcs",
            "comms",
            "gps",
            "payload",
            "cmd_logs",
        ]  # storage subsystem works differently so we need a separate list for it
        idx_list = [CDH_IDX, STORAGE_IDX]  # this is used to match the ss to the dh constants
        # get the latest data from each subsystem
        dh_data_list = [cls.get_dh_latest_data(x) for x in ss_list]  # storage subsytem works differently
        dh_storage_list = [cls.get_storage_info(x) for x in storage_ss_list]  # get the storage info for each subsystem

        # for each variable in the report, get the corresponding data from DH
        for ss in report.variables.keys():
            ss_lower = ss.lower()  # Create lowercase version for lookups

            if ss_lower == "storage":  # storage subsystem works differently so we skip it in this loop and handle it later
                continue

            if ss_lower not in ss_list:
                logger.warning(f"Subsystem {ss.upper()} not recognized for storage")
                continue

            dh_data = dh_data_list[ss_list.index(ss_lower)]
            if dh_data is None:
                logger.warning(f"No data for subsystem {ss.upper()} to pack in STORAGE")
                continue

            # iterating over all the variables for the ss in the report and adding them
            for var_name in report.variables[ss].keys():  # should have a function in telemetry_helper to get me this
                dh_var_idx = getattr(idx_list[ss_list.index(ss_lower)], var_name)
                report.add_variable(var_name, ss, dh_data[dh_var_idx])

        # itereate over all the variables in the report
        for var_name in report.variables["STORAGE"]:

            if var_name == "SD_TOTAL_USAGE":
                value = DH.SD_usage()  # get the SD card usage from DH
                report.add_variable(var_name, "STORAGE", value)
                continue

            # get the necessary dh names
            dh_ss_name = "_".join(var_name.split("_")[:-2]).lower()  # get the first 2/3 parts of the variable name
            dh_variable_name = "_".join(var_name.split("_")[-2:])  # get the last two parts of the variable name
            logger.info(
                f"Processing STORAGE var {var_name} with dh ss {dh_ss_name.upper()} and dh var {dh_variable_name.upper()}"
            )
            ss_index = storage_ss_list.index(dh_ss_name)
            if ss_index == -1:
                logger.warning(f"Subsystem {dh_ss_name.upper()} not recognized for storage variable {var_name}")
                continue

            if dh_storage_list[ss_index] is None:
                logger.warning(f"No data for subsystem {dh_ss_name.upper()} to pack in STORAGE variable {var_name}")
                continue

            dh_var_idx = getattr(STORAGE_IDX, dh_variable_name)  # get the index for the variable

            report.add_variable(var_name, "STORAGE", dh_storage_list[ss_index][dh_var_idx])  # add the variable to the report

        logger.debug(f"Packed STORAGE telemetry frame {report}")

        gc.collect()

        return report

    @classmethod
    def pack_tm_payload(cls):
        """
        Pack a payload telemetry frame.
        """
        # this will be a report
        report = Report("TM_PAYLOAD")

        ss_list = ["payload"]  # we need this to get the from dh, and it is case sensitive
        idx_list = [0]  # this is used to match the ss to the dh constants, payload only has 1 variable so idx is 0
        # get the latest data from each subsystem
        dh_data_list = [cls.get_dh_latest_data(x) for x in ss_list]

        # for each variable in the report, get the corresponding data from DH
        for ss in report.variables.keys():
            ss_lower = ss.lower()  # Create lowercase version for lookups
            if ss_lower not in ss_list:
                logger.warning(f"Subsystem {ss.upper()} not recognized for PAYLOAD")
                continue

            dh_data = dh_data_list[ss_list.index(ss_lower)]
            if dh_data is None:
                logger.warning(f"No data for subsystem {ss.upper()} to pack in PAYLOAD")
                continue

            # iterating over all the variables for the ss in the report and adding them
            for var_name in report.variables[ss].keys():
                dh_var_idx = idx_list[ss_list.index(ss_lower)]  # payload only has 1 variable so idx is 0
                report.add_variable(var_name, ss, dh_data[dh_var_idx])
        logger.debug(f"Packed PAYLOAD telemetry frame {report}")

        gc.collect()

        return report
