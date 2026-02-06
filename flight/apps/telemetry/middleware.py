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
    
from core import DataHandler as DH
from core.dh_constants import ADCS_IDX, CDH_IDX, EPS_IDX, GPS_IDX, STORAGE_IDX
from apps.telemetry.splat.splat.telemetry_codec import Report, pack, unpack 
from apps.telemetry.splat.splat.telemetry_helper import format_bytes
from core import logger



class Frame:
    
    """
    Representation of a frame of telemetry data. Replacing the old telemetry packer
    
    maybe will use this for more than telemetry later on
    """
    
    _TM_AVAILABLE = False
    _TM_FRAME_SIZE = const(248)     # this defines the maximum frame size

    # Pre-allocated frame buffer
    _FRAME = bytearray(_TM_FRAME_SIZE)   # [check] - not sure if preallocating is the best idea here. 
    # what about messages that are smaller


    @classmethod
    def FRAME(cls):
        return cls._FRAME

    @classmethod
    def FRAME_SIZE(cls):
        return cls._TM_FRAME_SIZE

    @classmethod
    def PACKET_LENGTH(cls):
        return cls._FRAME[3]

    @classmethod
    def TM_AVAILABLE(cls):
        return cls._TM_AVAILABLE

    @classmethod
    def TM_EXHAUSTED(cls):
        cls._TM_AVAILABLE = False
        
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
    def pack_tm_heartbeat(cls):
        """
        Pack a heartbeat telemetry frame into the pre-allocated FRAME buffer.
        """
        # this will be a report
        report = Report("TM_HEARTBEAT")
        
        ss_list = ["cdh", "eps", "adcs", "gps"]
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

        cls._FRAME[:] = pack(report)
        logger.debug(f"Packed heartbeat telemetry frame {format_bytes(cls._FRAME)}")
        # Mark telemetry as available
        cls._TM_AVAILABLE = True
        # print(f"Packed heartbeat telemetry frame {format_bytes(cls._FRAME)}")
        
        gc.collect()
        
        return True
    

    @classmethod
    def pack_tm_hal(cls):
        """
        Pack a HAL telemetry frame into the pre-allocated FRAME buffer.
        """
        print("Starting to pack HAL telemetry frame")
        # this will be a report
        report = Report("TM_HAL")
        
        ss_list = ["cdh", "eps", "storage"]
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
            print("  DH data:", dh_data)
            if dh_data is None:
                logger.warning(f"No data for subsystem {ss.upper()} to pack in HAL")
                continue
        
            # iterating over all the variables for the ss in the report and adding them
            for var_name in report.variables[ss].keys():
                dh_var_idx = getattr(idx_list[ss_list.index(ss_lower)], var_name)
                report.add_variable(var_name, ss, dh_data[dh_var_idx])

        cls._FRAME[:] = pack(report)
        # Mark telemetry as available
        cls._TM_AVAILABLE = True
        print(f"Packed HAL telemetry frame {format_bytes(cls._FRAME)}")
        
        gc.collect()
        
        return True
    
    
    