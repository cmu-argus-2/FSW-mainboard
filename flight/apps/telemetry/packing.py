"""
Telemetry Packer for Satellite (CircuitPython Compatible)

Packs telemetry data according to telemetry_config.py definitions
"""

import gc
try:
    from micropython import const
except ImportError:
    # Fallback for testing on regular Python
    def const(x):
        return x

from core.dh_constants import ADCS_IDX, CDH_IDX, EPS_IDX, GPS_IDX, STORAGE_IDX
from core import DataHandler as DH
from core import logger



# Convert to const for CircuitPython optimization
_TM_NOMINAL_SIZE = const(211)       # maybe this could be changed to be dynamic to decrease the number of changes
_TM_HAL_SIZE = const(46)            # necessary to update telemetry
_TM_STORAGE_SIZE = const(74)
_TM_PAYLOAD_SIZE = const(47)  # for now


class TelemetryPacker:
    """
    Packs telemetry data for transmission using format definitions from telemetry_config.py
    """

    _TM_AVAILABLE = False
    _TM_FRAME_SIZE = const(248)

    # Pre-allocated frame buffer
    _FRAME = bytearray(_TM_FRAME_SIZE)
    # _FRAME[0] = const(MSG_ID_SAT_HEARTBEAT) & 0xFF
    # _FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
    # _FRAME[3] = const(_TM_FRAME_SIZE) & 0xFF

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
    def _pack_field(cls, data, idx, field_format):
        """
        Pack a single field based on its format type
        
        Args:
            data: Data array to pack from
            idx: Index in data array
            field_format: Format character ('B', 'h', 'I', 'X', etc.)
        
        Returns:
            bytearray: Packed bytes
        """
        # if field_format == FORMAT_FIXED_POINT_HP:
        #     return convert_float_to_fixed_point_hp(data[idx])
        # elif field_format == FORMAT_FIXED_POINT_LP:
        #     return convert_float_to_fixed_point_lp(data[idx])
        # elif field_format == 'B':
        #     return bytearray([data[idx] & 0xFF])
        # elif field_format == 'H':
        #     return pack_unsigned_short_int(data, idx)
        # elif field_format == 'h':
        #     return pack_signed_short_int(data, idx)
        # elif field_format == 'I':
        #     return pack_unsigned_long_int(data, idx)
        # elif field_format == 'i':
        #     return pack_signed_long_int(data, idx)
        # else:
        #     logger.warning(f"Unknown format type: {field_format}")
        #     return bytearray([0x00])

    @classmethod
    def pack_tm_heartbeat(cls):
        """Pack nominal telemetry heartbeat using format from telemetry_config.py"""
        # if not cls._TM_AVAILABLE:
        #     cls._TM_AVAILABLE = True

        # # Initialize frame with header
        # cls._FRAME = bytearray(_TM_NOMINAL_SIZE + 4)
        # cls._FRAME[0] = const(MSG_ID_SAT_HEARTBEAT) & 0xFF
        # cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
        # cls._FRAME[3] = const(_TM_NOMINAL_SIZE) & 0xFF

        # offset = 4  # Start after header

        # ############ CDH fields ############
        # if DH.data_process_exists("cdh"):
        #     cdh_data = DH.get_latest_data("cdh")
            
        #     # print(f"time: {cdh_data[CDH_IDX.TIME]}")
        #     # print(f"scstate: {cdh_data[CDH_IDX.SC_STATE]}")
        #     # print(f"sd usage:{cdh_data[CDH_IDX.SD_USAGE]}")
        #     # print(f"ram_usage: {cdh_data[CDH_IDX.CURRENT_RAM_USAGE]}")
        #     # print(f"reboot count {cdh_data[CDH_IDX.REBOOT_COUNT]}")
        #     # print(f"watchdog timer {cdh_data[CDH_IDX.WATCHDOG_TIMER]}")
        #     # print(f"hal bitflags {cdh_data[CDH_IDX.HAL_BITFLAGS]}")
        #     # print(f"detumbling error flag {cdh_data[CDH_IDX.DETUMBLING_ERROR_FLAG]}")

        #     if cdh_data:
        #         for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["CDH"]:
        #             field_idx = getattr(CDH_IDX, field_name)
        #             packed = cls._pack_field(cdh_data, field_idx, field_format)
        #             cls._FRAME[offset:offset + len(packed)] = packed
        #             offset += len(packed)
        #     else:
        #         logger.warning("No latest CDH data available")
        # else:
        #     logger.warning("No CDH data available")

        # ############ EPS fields ############
        # if DH.data_process_exists("eps"):
        #     eps_data = DH.get_latest_data("eps")

        #     if eps_data:
        #         for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["EPS"]:
        #             field_idx = getattr(EPS_IDX, field_name)
        #             packed = cls._pack_field(eps_data, field_idx, field_format)
        #             cls._FRAME[offset:offset + len(packed)] = packed
        #             offset += len(packed)
        #     else:
        #         logger.warning("No latest EPS data available")
        # else:
        #     logger.warning("No EPS data available")

        # ############ ADCS fields ############
        # if DH.data_process_exists("adcs"):
        #     adcs_data = DH.get_latest_data("adcs")

        #     if adcs_data:
        #         for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["ADCS"]:
        #             field_idx = getattr(ADCS_IDX, field_name)
        #             packed = cls._pack_field(adcs_data, field_idx, field_format)
        #             cls._FRAME[offset:offset + len(packed)] = packed
        #             offset += len(packed)
        #     else:
        #         logger.warning("No latest ADCS data available")
        # else:
        #     logger.warning("No ADCS data available")

        # ############ GPS fields ############
        # if DH.data_process_exists("gps"):
        #     gps_data = DH.get_latest_data("gps")

        #     if gps_data:
        #         for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["GPS"]:
        #             # GPS fields need "GPS_" prefix
        #             field_idx = getattr(GPS_IDX, "GPS_" + field_name)
        #             packed = cls._pack_field(gps_data, field_idx, field_format)
        #             cls._FRAME[offset:offset + len(packed)] = packed
        #             offset += len(packed)
        #     else:
        #         logger.warning("No latest GPS data available")
        # else:
        #     logger.warning("No GPS data available")

        # cls._FRAME[:] = bytearray(cls._FRAME[:])
        # gc.collect()

        return True

    @classmethod
    def pack_tm_hal(cls):
        """Pack HAL telemetry using format from telemetry_config.py"""
    #     if not cls._TM_AVAILABLE:
    #         cls._TM_AVAILABLE = True

    #     cls._FRAME = bytearray(_TM_HAL_SIZE + 4)
    #     cls._FRAME[0] = const(MSG_ID_SAT_TM_HAL) & 0xFF
    #     cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
    #     cls._FRAME[3] = const(_TM_HAL_SIZE) & 0xFF

    #     offset = 4

    #     ############ CDH fields ############
    #     if DH.data_process_exists("cdh"):
    #         cdh_data = DH.get_latest_data("cdh")

    #         if cdh_data:
    #             for field_name, field_format in TM_HAL_FORMAT["CDH"]:
    #                 field_idx = getattr(CDH_IDX, field_name)
    #                 packed = cls._pack_field(cdh_data, field_idx, field_format)
    #                 cls._FRAME[offset:offset + len(packed)] = packed
    #                 offset += len(packed)
    #         else:
    #             logger.warning("No latest CDH data available")
    #     else:
    #         logger.warning("No CDH data available")

    #     cls._FRAME[:] = bytearray(cls._FRAME[:])
    #     gc.collect()

    #     return True

    # @classmethod
    # def pack_tm_storage(cls):
    #     """Pack storage telemetry using format from telemetry_config.py"""
    #     if not cls._TM_AVAILABLE:
    #         cls._TM_AVAILABLE = True

    #     cls._FRAME = bytearray(_TM_STORAGE_SIZE + 4)
    #     cls._FRAME[0] = const(MSG_ID_SAT_TM_STORAGE) & 0xFF
    #     cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
    #     cls._FRAME[3] = const(_TM_STORAGE_SIZE) & 0xFF

    #     offset = 4

    #     ############ CDH fields ############
    #     if DH.data_process_exists("cdh"):
    #         cdh_data = DH.get_latest_data("cdh")

    #         if cdh_data:
    #             for field_name, field_format in TM_STORAGE_FORMAT["CDH"]:
    #                 field_idx = getattr(CDH_IDX, field_name)
    #                 packed = cls._pack_field(cdh_data, field_idx, field_format)
    #                 cls._FRAME[offset:offset + len(packed)] = packed
    #                 offset += len(packed)
    #         else:
    #             logger.warning("No latest CDH data available")
    #     else:
    #         logger.warning("No CDH data available")

        # Total SD card usage
        cls._FRAME[18:22] = pack_unsigned_long_int([DH.SD_usage()], 0)

        ############ CDH fields ###########
        if DH.data_process_exists("cdh"):
            cdh_storage_info = DH.get_storage_info("cdh")
            # CDH number of files
            cls._FRAME[22:26] = pack_unsigned_long_int(cdh_storage_info, STORAGE_IDX.NUM_FILES)
            # CDH directory size
            cls._FRAME[26:30] = pack_unsigned_long_int(cdh_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("CDH Data process does not exist")

        ############ EPS fields ###########
        if DH.data_process_exists("eps"):
            eps_storage_info = DH.get_storage_info("eps")
            # EPS number of files
            cls._FRAME[30:34] = pack_unsigned_long_int(eps_storage_info, STORAGE_IDX.NUM_FILES)
            # EPS directory size
            cls._FRAME[34:38] = pack_unsigned_long_int(eps_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("EPS Data process does not exist")

        ############ ADCS fields ###########
        if DH.data_process_exists("adcs"):
            adcs_storage_info = DH.get_storage_info("adcs")
            # ADCS number of files
            cls._FRAME[38:42] = pack_unsigned_long_int(adcs_storage_info, STORAGE_IDX.NUM_FILES)
            # ADCS directory size
            cls._FRAME[42:46] = pack_unsigned_long_int(adcs_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("ADCS Data process does not exist")

        ############ COMMS fields ###########
        if DH.data_process_exists("comms"):
            comms_storage_info = DH.get_storage_info("comms")
            # COMMS number of files
            cls._FRAME[46:50] = pack_unsigned_long_int(comms_storage_info, STORAGE_IDX.NUM_FILES)
            # COMMS directory size
            cls._FRAME[50:54] = pack_unsigned_long_int(comms_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Comms Data process does not exist")

        ############ GPS fields ###########
        if DH.data_process_exists("gps"):
            gps_storage_info = DH.get_storage_info("gps")
            # GPS number of files
            cls._FRAME[54:58] = pack_unsigned_long_int(gps_storage_info, STORAGE_IDX.NUM_FILES)
            # GPS directory size
            cls._FRAME[58:62] = pack_unsigned_long_int(gps_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("GPS Data process does not exist")

        ############ Payload fields ###########
        # Nothing for now

        ############ Command fields ###########
        if DH.data_process_exists("cmd_logs"):
            cmd_logs_storage_info = DH.get_storage_info("cmd_logs")
            # Command logs number of files
            cls._FRAME[70:74] = pack_unsigned_long_int(cmd_logs_storage_info, STORAGE_IDX.NUM_FILES)
            # Command logs directory size
            cls._FRAME[74:78] = pack_unsigned_long_int(cmd_logs_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Command logs Data process does not exist")

    @classmethod
    def pack_tm_payload(cls):
        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        cls._FRAME = bytearray(_TM_PAYLOAD_SIZE + 4)  # pre-allocated buffer for packing
        cls._FRAME[0] = const(0x04) & 0xFF  # message ID
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
        cls._FRAME[3] = const(_TM_PAYLOAD_SIZE) & 0xFF  # packet length

        if DH.data_process_exists("payload_tm"):
            # payload_tm = DH.get_latest_data("payload_tm")

            ############ Payload device fields ###########

            ############ Payload controller fields ###########

            pass

    @classmethod
    def change_tm_id_nominal(cls):
        """Change message ID to TM_NOMINAL (for requested telemetry vs heartbeat)"""
        pass
        # cls._FRAME[0] = const(MSG_ID_SAT_TM_NOMINAL) & 0xFF