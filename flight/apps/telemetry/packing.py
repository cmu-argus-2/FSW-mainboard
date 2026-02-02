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

from apps.telemetry.constants import ADCS_IDX, CDH_IDX, EPS_IDX, GPS_IDX, STORAGE_IDX
from core import DataHandler as DH
from core import logger

# Import telemetry configuration and helpers
from apps.telemetry.tid.telemetry_definition import (
    HEARTBEAT_NOMINAL_FORMAT,
    TM_STORAGE_FORMAT,
    TM_HAL_FORMAT,
    FORMAT_FIXED_POINT_HP,
    FORMAT_FIXED_POINT_LP,
    MSG_ID_SAT_HEARTBEAT,
    MSG_ID_SAT_TM_HAL,
    MSG_ID_SAT_TM_STORAGE,
    MSG_ID_SAT_TM_NOMINAL,
)
from apps.telemetry.tid.telemetry_helper import (
    convert_float_to_fixed_point_hp,
    convert_float_to_fixed_point_lp,
    pack_signed_long_int,
    pack_signed_short_int,
    pack_unsigned_long_int,
    pack_unsigned_short_int,
)

# Convert to const for CircuitPython optimization
_TM_NOMINAL_SIZE = const(211)       # maybe this could be changed to be dynamic to decrease the number of changes
_TM_HAL_SIZE = const(46)            # necessary to update telemetry
_TM_STORAGE_SIZE = const(74)


class TelemetryPacker:
    """
    Packs telemetry data for transmission using format definitions from telemetry_config.py
    """

    _TM_AVAILABLE = False
    _TM_FRAME_SIZE = const(248)

    # Pre-allocated frame buffer
    _FRAME = bytearray(_TM_FRAME_SIZE)
    _FRAME[0] = const(MSG_ID_SAT_HEARTBEAT) & 0xFF
    _FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
    _FRAME[3] = const(_TM_FRAME_SIZE) & 0xFF

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
        if field_format == FORMAT_FIXED_POINT_HP:
            return convert_float_to_fixed_point_hp(data[idx])
        elif field_format == FORMAT_FIXED_POINT_LP:
            return convert_float_to_fixed_point_lp(data[idx])
        elif field_format == 'B':
            return bytearray([data[idx] & 0xFF])
        elif field_format == 'H':
            return pack_unsigned_short_int(data, idx)
        elif field_format == 'h':
            return pack_signed_short_int(data, idx)
        elif field_format == 'I':
            return pack_unsigned_long_int(data, idx)
        elif field_format == 'i':
            return pack_signed_long_int(data, idx)
        else:
            logger.warning(f"Unknown format type: {field_format}")
            return bytearray([0x00])

    @classmethod
    def pack_tm_heartbeat(cls):
        """Pack nominal telemetry heartbeat using format from telemetry_config.py"""
        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        # Initialize frame with header
        cls._FRAME = bytearray(_TM_NOMINAL_SIZE + 4)
        cls._FRAME[0] = const(MSG_ID_SAT_HEARTBEAT) & 0xFF
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
        cls._FRAME[3] = const(_TM_NOMINAL_SIZE) & 0xFF

        offset = 4  # Start after header

        ############ CDH fields ############
        if DH.data_process_exists("cdh"):
            cdh_data = DH.get_latest_data("cdh")
            
            # print(f"time: {cdh_data[CDH_IDX.TIME]}")
            # print(f"scstate: {cdh_data[CDH_IDX.SC_STATE]}")
            # print(f"sd usage:{cdh_data[CDH_IDX.SD_USAGE]}")
            # print(f"ram_usage: {cdh_data[CDH_IDX.CURRENT_RAM_USAGE]}")
            # print(f"reboot count {cdh_data[CDH_IDX.REBOOT_COUNT]}")
            # print(f"watchdog timer {cdh_data[CDH_IDX.WATCHDOG_TIMER]}")
            # print(f"hal bitflags {cdh_data[CDH_IDX.HAL_BITFLAGS]}")
            # print(f"detumbling error flag {cdh_data[CDH_IDX.DETUMBLING_ERROR_FLAG]}")

            if cdh_data:
                for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["CDH"]:
                    field_idx = getattr(CDH_IDX, field_name)
                    packed = cls._pack_field(cdh_data, field_idx, field_format)
                    cls._FRAME[offset:offset + len(packed)] = packed
                    offset += len(packed)
            else:
                logger.warning("No latest CDH data available")
        else:
            logger.warning("No CDH data available")

        ############ EPS fields ############
        if DH.data_process_exists("eps"):
            eps_data = DH.get_latest_data("eps")

            if eps_data:
                for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["EPS"]:
                    field_idx = getattr(EPS_IDX, field_name)
                    packed = cls._pack_field(eps_data, field_idx, field_format)
                    cls._FRAME[offset:offset + len(packed)] = packed
                    offset += len(packed)
            else:
                logger.warning("No latest EPS data available")
        else:
            logger.warning("No EPS data available")

        ############ ADCS fields ############
        if DH.data_process_exists("adcs"):
            adcs_data = DH.get_latest_data("adcs")

            if adcs_data:
                for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["ADCS"]:
                    field_idx = getattr(ADCS_IDX, field_name)
                    packed = cls._pack_field(adcs_data, field_idx, field_format)
                    cls._FRAME[offset:offset + len(packed)] = packed
                    offset += len(packed)
            else:
                logger.warning("No latest ADCS data available")
        else:
            logger.warning("No ADCS data available")

        ############ GPS fields ############
        if DH.data_process_exists("gps"):
            gps_data = DH.get_latest_data("gps")

            if gps_data:
                for field_name, field_format in HEARTBEAT_NOMINAL_FORMAT["GPS"]:
                    # GPS fields need "GPS_" prefix
                    field_idx = getattr(GPS_IDX, "GPS_" + field_name)
                    packed = cls._pack_field(gps_data, field_idx, field_format)
                    cls._FRAME[offset:offset + len(packed)] = packed
                    offset += len(packed)
            else:
                logger.warning("No latest GPS data available")
        else:
            logger.warning("No GPS data available")

        cls._FRAME[:] = bytearray(cls._FRAME[:])
        gc.collect()

        return True

    @classmethod
    def pack_tm_hal(cls):
        """Pack HAL telemetry using format from telemetry_config.py"""
        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        cls._FRAME = bytearray(_TM_HAL_SIZE + 4)
        cls._FRAME[0] = const(MSG_ID_SAT_TM_HAL) & 0xFF
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
        cls._FRAME[3] = const(_TM_HAL_SIZE) & 0xFF

        offset = 4

        ############ CDH fields ############
        if DH.data_process_exists("cdh"):
            cdh_data = DH.get_latest_data("cdh")

            if cdh_data:
                for field_name, field_format in TM_HAL_FORMAT["CDH"]:
                    field_idx = getattr(CDH_IDX, field_name)
                    packed = cls._pack_field(cdh_data, field_idx, field_format)
                    cls._FRAME[offset:offset + len(packed)] = packed
                    offset += len(packed)
            else:
                logger.warning("No latest CDH data available")
        else:
            logger.warning("No CDH data available")

        cls._FRAME[:] = bytearray(cls._FRAME[:])
        gc.collect()

        return True

    @classmethod
    def pack_tm_storage(cls):
        """Pack storage telemetry using format from telemetry_config.py"""
        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        cls._FRAME = bytearray(_TM_STORAGE_SIZE + 4)
        cls._FRAME[0] = const(MSG_ID_SAT_TM_STORAGE) & 0xFF
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)
        cls._FRAME[3] = const(_TM_STORAGE_SIZE) & 0xFF

        offset = 4

        ############ CDH fields ############
        if DH.data_process_exists("cdh"):
            cdh_data = DH.get_latest_data("cdh")

            if cdh_data:
                for field_name, field_format in TM_STORAGE_FORMAT["CDH"]:
                    field_idx = getattr(CDH_IDX, field_name)
                    packed = cls._pack_field(cdh_data, field_idx, field_format)
                    cls._FRAME[offset:offset + len(packed)] = packed
                    offset += len(packed)
            else:
                logger.warning("No latest CDH data available")
        else:
            logger.warning("No CDH data available")

        # Total SD card usage
        cls._FRAME[offset:offset + 4] = pack_unsigned_long_int([DH.SD_usage()], 0)
        offset += 4

        ############ Storage info for each subsystem ############
        storage_subsystems = [
            ("cdh", "CDH"),
            ("eps", "EPS"),
            ("adcs", "ADCS"),
            ("comms", "COMMS"),
            ("gps", "GPS"),
            ("payload", "PAYLOAD"),
            ("cmd_logs", "COMMAND"),
        ]

        for dh_name, prefix in storage_subsystems:
            if DH.data_process_exists(dh_name):
                storage_info = DH.get_storage_info(dh_name)
                # Pack NUM_FILES
                cls._FRAME[offset:offset + 4] = pack_unsigned_long_int(
                    storage_info, STORAGE_IDX.NUM_FILES
                )
                offset += 4
                # Pack DIR_SIZE
                cls._FRAME[offset:offset + 4] = pack_unsigned_long_int(
                    storage_info, STORAGE_IDX.DIR_SIZE
                )
                offset += 4
            else:
                logger.warning(f"{dh_name} Data process does not exist")
                # Write zeros for missing data
                cls._FRAME[offset:offset + 8] = bytearray([0x00] * 8)
                offset += 8

        cls._FRAME[:] = bytearray(cls._FRAME[:])
        gc.collect()

        return True

    @classmethod
    def pack_tm_payload(cls):
        """Pack payload telemetry (TODO)"""
        pass

    @classmethod
    def change_tm_id_nominal(cls):
        """Change message ID to TM_NOMINAL (for requested telemetry vs heartbeat)"""
        cls._FRAME[0] = const(MSG_ID_SAT_TM_NOMINAL) & 0xFF