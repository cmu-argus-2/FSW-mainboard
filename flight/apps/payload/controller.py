"""
Payload Control Interface

This module defines the Payload Controller class, which is responsible for managing the main interface between
the host and the Payload.

Author: Ibrahima Sory Sow, Perrin Tong

"""

from apps.payload.definitions import (
    CommandID,
    ErrorCodes,
    ExternalRequest,
    FileTransfer,
    FileTransferType,
    ODStatus,
    PayloadTM,
    Resp_RequestNextFilePacket,
)
from apps.payload.protocol import Decoder, Encoder
from apps.telemetry.constants import PAYLOAD_IDX
from core import DataHandler as DH
from core import logger
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE
from micropython import const

_PING_RESP_VALUE = const(0x60)  # DO NOT CHANGE THIS VALUE


class PayloadState:  # Only from the host perspective
    OFF = 0  # Fully powered down
    POWERING_ON = 1  # Power and boot sequence started
    READY = 2  # Fully operational
    SHUTTING_DOWN = 3  # Graceful shutdown in progress


def map_state(state):
    """
    Maps the state to its string representation.
    """
    if state == PayloadState.OFF:
        return "OFF"
    elif state == PayloadState.POWERING_ON:
        return "POWERING_ON"
    elif state == PayloadState.READY:
        return "READY"
    elif state == PayloadState.SHUTTING_DOWN:
        return "SHUTTING_DOWN"
    else:
        return "UNKNOWN"


class PayloadController:

    # Bi-directional communication interface
    communication_interface = None
    _interface_injected = False

    # State of the Payload from the host perspective
    state = PayloadState.OFF

    # Last error (from the host perspective)
    last_error = ErrorCodes.OK

    # Contains the last command IDs sent to the Payload
    cmd_sent = 0
    last_cmd_sent = None  # Track the last command ID sent
    timestamp_cmd_sent = 0

    # No response counter
    no_resp_counter = 0

    # Boot variables
    time_we_started_booting = 0
    TIMEOUT_BOOT = 120  # seconds

    # Timeout for the shutdown process
    TIMEOUT_SHUTDOWN = 10  # 10 seconds
    time_we_sent_shutdown = 0
    need_shutdown = False
    payload_sw_has_shutdown = False  # Flag to check if the payload has shutdown properly

    # Current request
    current_request = ExternalRequest.NO_ACTION
    timestamp_request = 0

    # Telemetry variables
    payload_tm_data_format = "QQQ" + 12 * "B" + 13 * "B" + 3 * "H"
    tm_process_data_format = payload_tm_data_format + "LBBBB"
    log_data = [0] * len(tm_process_data_format)
    _prev_tm_time = TPM.monotonic()
    _now = TPM.monotonic()
    telemetry_period = const(10)  # seconds
    _not_waiting_tm_response = False

    # File transfer
    no_more_file_packet_to_receive = False
    just_requested_file_packet = False

    # Packet retry mechanism for CRC failures
    packet_retry_count = 0
    MAX_PACKET_RETRIES = 3

    # Communication statistics
    crc_failure_count = 0
    total_packets_received = 0
    total_packets_retried = 0
    packets_skipped_after_max_retries = 0  # Packets filled with zeros due to persistent CRC failures

    # OD variables
    od_status: ODStatus = None

    # (re-)boot variables
    must_re_attempt_boot = False
    attempting_reboot = False

    # Power control of the payload
    # en_pin = None

    @classmethod
    def load_communication_interface(cls):
        # This function is called from the HAL to load the communication interface
        # This is done only once at startup
        if cls._interface_injected:
            logger.info("Communication interface already injected. Skipping injection.")
            return

        # Using build flag
        # if SATELLITE.BUILD == "FLIGHT":
        from apps.payload.uart_comms import PayloadUART

        cls.communication_interface = PayloadUART
        cls._interface_injected = True
        logger.info("Payload UART communication interface injected.")

        # elif SATELLITE.BUILD == "SIL":
        #     from apps.payload.ipc_comms import PayloadIPC

        #     cls.communication_interface = PayloadIPC
        #     cls._interface_injected = True
        #     logger.info("Payload IPC communication interface injected.")

        assert cls.communication_interface is not None, "Communication interface not injected. Cannot initialize controller."

    @classmethod
    def initialize(cls):
        if cls._interface_injected:
            return cls.communication_interface.connect()
        else:
            logger.error("Communication interface not injected yet.")
            return False

    @classmethod
    def deinitialize(cls):
        cls.communication_interface.disconnect()

    @classmethod
    def interface_injected(cls):
        return cls._interface_injected

    @classmethod
    def _did_we_send_a_command(cls):
        # TODO: add logic for retry here
        return cls.cmd_sent > 0

    @classmethod
    def add_request(cls, request: ExternalRequest) -> bool:
        if not isinstance(request, int) or request < ExternalRequest.NO_ACTION or request >= ExternalRequest.INVALID:
            # Invalid request
            logger.error(f"Invalid request: {request}")
            # TODO: add if a request is already being processed
            return False
        cls.current_request = request
        cls.timestamp_request = TPM.monotonic()
        return True

    @classmethod
    def _clear_request(cls):
        cls.current_request = ExternalRequest.NO_ACTION
        cls.timestamp_request = 0

    @classmethod
    def cancel_current_request(cls):
        if cls.state != PayloadState.READY:
            cls._clear_request()
            # TODO: need to add a specific logic to cancel the request
            # This should be used only when the payload is is not READY.
            # If in READY, it would have already been executing the request
            return True
        else:
            # Log
            return False

    @classmethod
    def handle_external_requests(cls):

        if cls.current_request == ExternalRequest.NO_ACTION:
            pass

        elif cls.current_request == ExternalRequest.TURN_ON:
            cls._switch_to_state(PayloadState.POWERING_ON)
            cls._clear_request()

        elif cls.current_request == ExternalRequest.TURN_OFF:
            cls._switch_to_state(PayloadState.SHUTTING_DOWN)
            cls.shutdown()
            cls._clear_request()

        elif cls.current_request == ExternalRequest.REBOOT:
            logger.info("Rebooting the Payload...")
            cls.attempting_reboot = True
            cls.shutdown()
            cls._switch_to_state(PayloadState.SHUTTING_DOWN)
            cls._clear_request()

        elif cls.current_request == ExternalRequest.CLEAR_STORAGE:
            # coming soon, after payload updates
            pass

        elif cls.current_request == ExternalRequest.REQUEST_IMAGE:
            logger.info("An image has been requested...")
            if cls.file_transfer_in_progress():
                logger.error("File transfer already in progress. Cannot request image.")
                return

            if not DH.file_process_exists("img"):
                logger.error("Image file process not found. Cannot request image.")
                return

            cls.request_image_transfer()
            cls._clear_request()

        elif cls.current_request == ExternalRequest.FORCE_POWER_OFF:
            # This is a last resort
            cls.turn_off_power()
            cls._switch_to_state(PayloadState.OFF)
            cls._clear_request()

    @classmethod
    def _switch_to_state(cls, new_state: PayloadState):
        if new_state != cls.state:
            cls.state = new_state
            logger.info(f"[PAYLOAD] Switching to state {map_state(new_state)}...")
            if new_state == PayloadState.READY:
                # clearing variables
                cls.must_re_attempt_boot = False
                cls.attempting_reboot = False
                cls.time_we_started_booting = 0
                cls.payload_sw_has_shutdown = False

    @classmethod
    def run_control_logic(cls):
        # Move this potentially at the task level
        cls._now = TPM.monotonic()

        # Check for requests
        cls.handle_external_requests()

        if cls.state == PayloadState.OFF:
            # Do nothing
            # Make sure the power line is off
            cls.turn_off_power()

            if cls.must_re_attempt_boot:
                # We have timed out while booting
                # Log error and reset the state
                logger.error("Timeout booting. Resetting state.")
                cls._switch_to_staate(PayloadState.POWERING_ON)

        elif cls.state == PayloadState.POWERING_ON:
            # Wait for the Payload to be ready
            cls.turn_on_power()

            if cls.time_we_started_booting == 0:
                cls.time_we_started_booting = cls._now

            if not cls.communication_interface.is_connected():
                if cls._interface_injected:
                    cls.initialize()
                else:
                    logger.error("Communication interface not injected yet.")
            else:
                logger.info("Communication interface is connected.")

                # The serial link will be purged by the payload when it opens its channel
                # so we ping to check until it is ready, i.e. the ping response is received
                if cls.ping():
                    cls._switch_to_state(PayloadState.READY)
                    logger.info(f"Payload is ready. Full boot in  {cls._now - cls.time_we_started_booting} seconds.")
                    cls.time_we_started_booting = 0  # Reset the boot time
                elif (
                    cls._now - cls.time_we_started_booting > cls.TIMEOUT_BOOT
                ):  # we seemingly failed --> attempt again to turn on
                    cls.turn_off_power()  # turn off the power line, just in case
                    cls._switch_to_state(PayloadState.OFF)  # Switch to OFF state
                    cls.last_error = ErrorCodes.TIMEOUT_BOOT  # Log error
                    cls.time_we_started_booting = 0  # Reset the boot time
                    # CDH / HAL notification
                    cls.must_re_attempt_boot = True  # Set the flag to re-attempt booting

        elif cls.state == PayloadState.READY:

            # logger.info(f"Is a command pending? {cls._did_we_send_a_command()}")
            # logger.info(f"Cmd sent: {cls.cmd_sent}")

            if not cls._did_we_send_a_command():  # Add timeout for retry
                # Check for telemetry (but not during active file transfer)
                if (
                    not FileTransfer.in_progress
                    and cls._now - cls._prev_tm_time > cls.telemetry_period
                    and not cls._not_waiting_tm_response
                ):
                    cls.request_telemetry()

            if not cls._did_we_send_a_command():  # Add timeout for retry
                if FileTransfer.in_progress:
                    # Check if we need to request the next file packet
                    if not cls.just_requested_file_packet:
                        cls.request_next_file_packet()

            # Coming soon :)
            # Check OD states
            # For now, just ping the OD status

            cls.receive_response()

        elif cls.state == PayloadState.SHUTTING_DOWN:
            # Wait for the Payload to shutdown

            cls.receive_response()

            if cls.payload_sw_has_shutdown:
                logger.info("Payload SW has shutdown properly.")
                cls.turn_off_power()
                cls._switch_to_state(PayloadState.OFF)

            if cls.time_we_sent_shutdown + cls.TIMEOUT_SHUTDOWN < TPM.monotonic():
                # We have waited too long
                # Force the shutdown by cutting the power
                cls.turn_off_power()
                logger.warning("Timeout while shutting down. Force shutdown.")
                cls.last_error = ErrorCodes.TIMEOUT_SHUTDOWN

    @classmethod
    def receive_response(cls):
        # Poll for response with timeout
        timeout = 0.015  # 15ms timeout
        poll_interval = 0.001  # Check every 1ms
        start_time = TPM.monotonic()

        recv = bytearray()
        while TPM.monotonic() - start_time < timeout:
            recv = cls.communication_interface.receive()
            if recv:
                # Check if this is the response we're expecting
                if cls.last_cmd_sent is not None:
                    # Peek at command ID (first byte of packet)
                    if len(recv) >= 1:
                        received_cmd_id = recv[0]
                        if received_cmd_id != cls.last_cmd_sent:
                            logger.warning(
                                f"[DEBUG] Skipping mismatched response: "
                                f"expected cmd_id={cls.last_cmd_sent:02x}, got {received_cmd_id:02x}"
                            )
                            recv = bytearray()  # Clear and continue polling
                            continue
                # Got the right response!
                break
            TPM.sleep(poll_interval)

        logger.info(f"[DEBUG] receive_response() called, recv length: {len(recv) if recv else 0}")

        if recv:
            res = Decoder.decode(recv)
            cls.cmd_sent -= 1
            cls.last_cmd_sent = None  # Clear after receiving
        else:
            res = ErrorCodes.NO_RESPONSE
        return cls.handle_responses(res)

    @classmethod
    def handle_responses(cls, resp):
        """
        Handle the status of the responses received from the Payload.
        """
        if resp:  # there is a response
            sent_cmd_id = Decoder.current_command_id()

            if sent_cmd_id == CommandID.REQUEST_TELEMETRY and resp == ErrorCodes.OK:
                cls._prev_tm_time = cls._now
                cls._not_waiting_tm_response = False
                cls.log_telemetry()
                return True

            elif sent_cmd_id == CommandID.REQUEST_IMAGE and resp == ErrorCodes.OK:
                # Start the file transfer
                FileTransfer.start_transfer(FileTransferType.IMAGE)
                logger.info("File transfer started.")
                cls.just_requested_file_packet = False
                cls.packet_retry_count = 0  # Reset retry counter for new transfer
                cls.packets_skipped_after_max_retries = 0  # Reset skip counter
                cls.cmd_sent = 0  # Reset command counter to allow file packet requests
                return True

            elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.OK:
                # Continue the file transfer, packet received successfully
                cls.just_requested_file_packet = False
                cls.packet_retry_count = 0  # Reset retry counter on success
                cls.total_packets_received += 1
                cls.cmd_sent = 0  # Reset command counter to allow next packet request

                # Log the received packet data (only actual payload)
                DH.log_file("img", Resp_RequestNextFilePacket.received_data[: Resp_RequestNextFilePacket.received_data_size])
                FileTransfer.ack_packet()  # increment the counter to next packet
                return True

            elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.INVALID_PACKET:
                # CRC verification failed or packet corrupted - retry same packet
                cls.packet_retry_count += 1
                cls.crc_failure_count += 1
                cls.just_requested_file_packet = False  # Allow retry

                if cls.packet_retry_count >= cls.MAX_PACKET_RETRIES:
                    # Max retries exceeded, skip this packet and continue with rest of file
                    logger.error(
                        f"CRC failed {cls.MAX_PACKET_RETRIES} times for packet "
                        f"{FileTransfer.packet_nb}, inserting empty packet and continuing"
                    )

                    # Log empty 240-byte packet to mark the corrupted/missing data
                    empty_packet = bytearray(240)  # All zeros
                    DH.log_file("img", empty_packet)

                    cls.packets_skipped_after_max_retries += 1

                    # Move to next packet
                    FileTransfer.ack_packet()
                    cls.packet_retry_count = 0  # Reset retry counter for next packet
                    cls.last_error = ErrorCodes.INVALID_PACKET  # Still track that we had an error

                    return False  # Indicate error occurred, but continue transfer
                else:
                    # Retry the same packet (don't increment packet_nb)
                    cls.total_packets_retried += 1
                    logger.warning(
                        f"CRC failed for packet {FileTransfer.packet_nb}, "
                        f"retry {cls.packet_retry_count}/{cls.MAX_PACKET_RETRIES}"
                    )
                    # DON'T call FileTransfer.ack_packet() - we want to retry the SAME packet
                    return False

            elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.NO_RESPONSE:
                # No response or incomplete packet received - retry same packet
                cls.packet_retry_count += 1
                cls.just_requested_file_packet = False  # Allow retry

                if cls.packet_retry_count >= cls.MAX_PACKET_RETRIES:
                    # Max retries exceeded, skip this packet
                    logger.error(
                        f"No response {cls.MAX_PACKET_RETRIES} times for packet "
                        f"{FileTransfer.packet_nb}, inserting empty packet and continuing"
                    )

                    # Log empty 240-byte packet
                    empty_packet = bytearray(240)
                    DH.log_file("img", empty_packet)

                    cls.packets_skipped_after_max_retries += 1

                    # Move to next packet
                    FileTransfer.ack_packet()
                    cls.packet_retry_count = 0

                    return False
                else:
                    # Retry the same packet
                    cls.total_packets_retried += 1
                    logger.warning(
                        f"No response for packet {FileTransfer.packet_nb}, "
                        f"retry {cls.packet_retry_count}/{cls.MAX_PACKET_RETRIES}"
                    )
                    return False

            elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.NO_MORE_FILE_PACKET:
                cls.no_more_file_packet_to_receive = True
                FileTransfer.stop_transfer()
                DH.file_completed("img")

                # Log comprehensive transfer statistics
                if cls.packets_skipped_after_max_retries > 0:
                    logger.warning(
                        f"Completed image transfer with CORRUPTION: "
                        f"{cls.total_packets_received} packets received, "
                        f"{cls.packets_skipped_after_max_retries} packets corrupted (filled with zeros), "
                        f"{cls.crc_failure_count} total CRC failures, "
                        f"{cls.total_packets_retried} retries"
                    )
                else:
                    logger.info(
                        f"Completed image transfer: {cls.total_packets_received} packets, "
                        f"{cls.crc_failure_count} CRC failures, {cls.total_packets_retried} retries"
                    )

                # Reset statistics for next transfer
                cls.crc_failure_count = 0
                cls.total_packets_received = 0
                cls.total_packets_retried = 0
                cls.packets_skipped_after_max_retries = 0
                cls.packet_retry_count = 0
                return True

            elif sent_cmd_id == CommandID.SHUTDOWN and resp == ErrorCodes.OK:
                # Paylaod has confirmed that we have properly shutdown
                # Now we can safely turn off the power line, which we will do in the main run logic
                cls.payload_sw_has_shutdown = True

            else:
                logger.error(f"Command error received: {resp}")  # TODO: map to good string for logging purposes
                cls.last_error = resp
                return False
        return False

    @classmethod
    def ping(cls):
        cls.communication_interface.send(Encoder.encode_ping())
        cls.last_cmd_sent = CommandID.PING  # Track command
        resp = cls.communication_interface.receive()
        if resp:  # a ping is immediate so if we don't receive a response, we assume it is not connected
            return Decoder.decode(resp) == _PING_RESP_VALUE
        return False

    @classmethod
    def shutdown(cls):
        # Simply send the shutdown command
        cls.communication_interface.send(Encoder.encode_shutdown())
        cls.cmd_sent += 1
        cls.last_cmd_sent = CommandID.SHUTDOWN  # Track command
        cls.time_we_sent_shutdown = TPM.monotonic()

    @classmethod
    def request_telemetry(cls):
        logger.info("Requesting telemetry...")
        cls.communication_interface.send(Encoder.encode_request_telemetry())
        cls.cmd_sent += 1
        cls.last_cmd_sent = CommandID.REQUEST_TELEMETRY  # Track command
        cls._not_waiting_tm_response = True

    @classmethod
    def log_telemetry(cls):
        PayloadTM.print()
        if DH.data_process_exists("payload_tm"):
            cls.log_data[PAYLOAD_IDX.SYSTEM_TIME] = int(PayloadTM.SYSTEM_TIME)
            cls.log_data[PAYLOAD_IDX.SYSTEM_UPTIME] = int(PayloadTM.SYSTEM_UPTIME)
            cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_TIME] = int(PayloadTM.LAST_EXECUTED_CMD_TIME)
            cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_ID] = int(PayloadTM.LAST_EXECUTED_CMD_ID)
            cls.log_data[PAYLOAD_IDX.PAYLOAD_STATE] = int(PayloadTM.PAYLOAD_STATE)
            cls.log_data[PAYLOAD_IDX.ACTIVE_CAMERAS] = int(PayloadTM.ACTIVE_CAMERAS)
            cls.log_data[PAYLOAD_IDX.CAPTURE_MODE] = int(PayloadTM.CAPTURE_MODE)
            cls.log_data[PAYLOAD_IDX.CAM_STATUS_0] = int(PayloadTM.CAM_STATUS[0])
            cls.log_data[PAYLOAD_IDX.CAM_STATUS_1] = int(PayloadTM.CAM_STATUS[1])
            cls.log_data[PAYLOAD_IDX.CAM_STATUS_2] = int(PayloadTM.CAM_STATUS[2])
            cls.log_data[PAYLOAD_IDX.CAM_STATUS_3] = int(PayloadTM.CAM_STATUS[3])
            cls.log_data[PAYLOAD_IDX.IMU_STATUS] = int(PayloadTM.IMU_STATUS)
            cls.log_data[PAYLOAD_IDX.TASKS_IN_EXECUTION] = int(PayloadTM.TASKS_IN_EXECUTION)
            cls.log_data[PAYLOAD_IDX.DISK_USAGE] = int(PayloadTM.DISK_USAGE)
            cls.log_data[PAYLOAD_IDX.LATEST_ERROR] = int(cls.last_error)
            cls.log_data[PAYLOAD_IDX.TEGRASTATS_PROCESS_STATUS] = int(PayloadTM.TEGRASTATS_PROCESS_STATUS)
            cls.log_data[PAYLOAD_IDX.RAM_USAGE] = int(PayloadTM.RAM_USAGE)
            cls.log_data[PAYLOAD_IDX.SWAP_USAGE] = int(PayloadTM.SWAP_USAGE)
            cls.log_data[PAYLOAD_IDX.ACTIVE_CORES] = int(PayloadTM.ACTIVE_CORES)
            cls.log_data[PAYLOAD_IDX.CPU_LOAD_0] = int(PayloadTM.CPU_LOAD[0])
            cls.log_data[PAYLOAD_IDX.CPU_LOAD_1] = int(PayloadTM.CPU_LOAD[1])
            cls.log_data[PAYLOAD_IDX.CPU_LOAD_2] = int(PayloadTM.CPU_LOAD[2])
            cls.log_data[PAYLOAD_IDX.CPU_LOAD_3] = int(PayloadTM.CPU_LOAD[3])
            cls.log_data[PAYLOAD_IDX.CPU_LOAD_4] = int(PayloadTM.CPU_LOAD[4])
            cls.log_data[PAYLOAD_IDX.CPU_LOAD_5] = int(PayloadTM.CPU_LOAD[5])
            cls.log_data[PAYLOAD_IDX.GPU_FREQ] = int(PayloadTM.GPU_FREQ)
            cls.log_data[PAYLOAD_IDX.CPU_TEMP] = int(PayloadTM.CPU_TEMP)
            cls.log_data[PAYLOAD_IDX.GPU_TEMP] = int(PayloadTM.GPU_TEMP)
            cls.log_data[PAYLOAD_IDX.VDD_IN] = int(PayloadTM.VDD_IN)
            cls.log_data[PAYLOAD_IDX.VDD_CPU_GPU_CV] = int(PayloadTM.VDD_CPU_GPU_CV)
            cls.log_data[PAYLOAD_IDX.VDD_SOC] = int(PayloadTM.VDD_SOC)

            cls.log_data[PAYLOAD_IDX.TIME_PAYLOAD_CONTROLLER] = TPM.time()
            cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_STATE] = int(cls.state)
            cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_COMMUNICATION_INTERFACE_ID] = (
                cls._return_communication_interface_id() if cls._interface_injected else 0
            )
            cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_COMMUNICATION_INTERFACE_CONNECTED] = int(
                cls.communication_interface.is_connected()
            )
            cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_LAST_ERROR] = int(cls.last_error) if cls.last_error else 0

            DH.log_data("payload_tm", cls.log_data)

    @classmethod
    def _return_communication_interface_id(cls):
        if cls._interface_injected:
            return int(cls.communication_interface.get_id())
        else:
            logger.error("Communication interface not injected yet.")
            return None

    @classmethod
    def enable_cameras(cls):
        cls.communication_interface.send(Encoder.encode_enable_cameras())
        cls.cmd_sent += 1
        cls.last_cmd_sent = CommandID.ENABLE_CAMERAS  # Track command

    @classmethod
    def disable_cameras(cls):
        cls.communication_interface.send(Encoder.encode_disable_cameras())
        cls.cmd_sent += 1
        cls.last_cmd_sent = CommandID.DISABLE_CAMERAS  # Track command

    @classmethod
    def request_image_transfer(cls):
        # This starts the process for image transfer which will be executed in the background by the controller at each cycle
        if cls.state != PayloadState.READY:
            logger.error("Cannot request image transfer. Payload is not ready.")
            return False

        # Don't request new image if transfer already in progress
        if FileTransfer.in_progress:
            logger.warning("Image transfer already in progress, ignoring duplicate request")
            return False

        cmd_bytes = Encoder.encode_request_image()
        hex_str = " ".join(f"{b:02x}" for b in cmd_bytes[:10])
        logger.info(f"[DEBUG TX] Sending REQUEST_IMAGE command: {hex_str}")
        cls.communication_interface.send(cmd_bytes)
        cls.cmd_sent += 1
        cls.last_cmd_sent = CommandID.REQUEST_IMAGE  # Track command
        cls.no_more_file_packet_to_receive = False
        return True

    @classmethod
    def request_next_file_packet(cls):
        if cls.state != PayloadState.READY:
            logger.error("Cannot request next file packet. Payload is not ready.")
            return False

        if not cls.just_requested_file_packet:
            # Flush buffer before requesting file packet to clear any stale PING_ACKs
            cls.communication_interface.flush_rx_buffer()
            cls.communication_interface.send(Encoder.encode_request_next_file_packet(FileTransfer.packet_nb))
            cls.cmd_sent += 1
            cls.last_cmd_sent = CommandID.REQUEST_NEXT_FILE_PACKET  # Track command
            cls.just_requested_file_packet = True
            logger.info(f"Requesting next file packet {FileTransfer.packet_nb}...")
            return True

    @classmethod
    def file_transfer_in_progress(cls):
        return FileTransfer.in_progress

    @classmethod
    def turn_on_power(cls):
        # This should enable the power line
        # If the function is called again and the power line is already on, it SHOULD do nothing
        # This will be called multiple times in a row
        logger.debug("[PAYLOAD] Turning on power...")
        pass

    @classmethod
    def turn_off_power(cls):
        # This is an expensive and drastic operation on the HW so must be limited to strict necessity
        # Preferable after a shutdown command
        logger.debug("[PAYLOAD] Turning off power...")
        pass
