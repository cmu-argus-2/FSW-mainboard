"""
Payload Control Interface

This module defines the Payload Controller class, which is responsible for managing the main interface between
the host and the Payload.

Author: Ibrahima Sory Sow

"""

import time

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
from core import DataHandler as DH
from core import logger
from hal.configuration import SATELLITE
from micropython import const

_PING_RESP_VALUE = const(0x60)  # DO NOT CHANGE THIS VALUE


class PayloadState:  # Only from the host perspective
    OFF = 0  # Fully powered down
    POWERING_ON = 1  # Power and boot sequence started
    READY = 2  # Fully operational
    SHUTTING_DOWN = 3  # Graceful shutdown in progress
    REBOOTING = 4  # Going through shutdown + boot


class PayloadController:

    # Bi-directional communication interface
    communication_interface = None
    _interface_injected = False

    # State of the Payload from the host perspective
    state = PayloadState.OFF

    # Last error (from the host perspective)
    last_error = None

    # Contains the last command IDs sent to the Payload
    cmd_sent = 0
    timestamp_cmd_sent = 0

    # No response counter
    no_resp_counter = 0

    # Boot variables
    time_we_started_booting = 0
    TIMEOUT_BOOT = 120  # seconds

    # Timeout for the shutdown process
    TIMEOUT_SHUTDOWN = 10  # 10 seconds
    time_we_sent_shutdown = 0

    # Current request
    current_request = ExternalRequest.NO_ACTION
    timestamp_request = 0

    # Last telemetry received
    _prev_tm_time = time.monotonic()
    _now = time.monotonic()
    telemetry_period = const(10)  # seconds
    _not_waiting_tm_response = False

    # File transfer
    no_more_file_packet_to_receive = False
    just_requested_file_packet = False

    # OD variables
    od_status: ODStatus = None

    # Reboot variables
    attempting_reboot = False

    # Power control
    # en_pin = None

    @classmethod
    def load_communication_interface(cls):
        # This function is called from the HAL to load the communication interface
        # This is done only once at startup
        if cls._interface_injected:
            logger.info("Communication interface already injected. Skipping injection.")
            return

        # Using build flag
        if SATELLITE.BUILD == "FLIGHT":
            from apps.payload.uart_comms import PayloadUART

            cls.communication_interface = PayloadUART
            cls._interface_injected = True
            logger.info("Payload UART communication interface injected.")

        elif SATELLITE.BUILD == "SIL":
            from apps.payload.ipc_comms import PayloadIPC

            cls.communication_interface = PayloadIPC
            cls._interface_injected = True
            logger.info("Payload IPC communication interface injected.")

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
            # log error
            # TODO: add if a request is already being processed
            return False
        cls.current_request = request
        cls.timestamp_request = time.monotonic()
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
            cls._clear_request()

        elif cls.current_request == ExternalRequest.REBOOT:
            cls._switch_to_state(PayloadState.REBOOTING)
            cls._clear_request()

        elif cls.current_request == ExternalRequest.CLEAR_STORAGE:
            # coming soon, after payload updates
            pass

        elif cls.current_request == ExternalRequest.REQUEST_IMAGE:
            logger.info("An image has been requested...")
            if cls.file_transfer_in_progress():
                logger.error("File transfer already in progress. Cannot request image.")
                return

            if not DH.data_process_exists("img"):
                logger.error("Image data process not found. Cannot request image.")
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
            # Log state change

    @classmethod
    def run_control_logic(cls):
        # Move this potentially at the task level
        cls._now = time.monotonic()

        # Check for requests
        cls.handle_external_requests()

        if cls.state == PayloadState.OFF:
            # Do nothing unless it's time to power on
            pass

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
                elif cls._now - cls.time_we_started_booting > cls.TIMEOUT_BOOT:
                    pass
                else:  # we failed
                    cls.turn_off_power()  # turn off the power line, just in case
                    cls.last_error = ErrorCodes.TIMEOUT_BOOT  # Log error
                    cls.time_we_started_booting = 0  # Reset the boot time
                    # CDH / HAL notification

        elif cls.state == PayloadState.READY:

            # logger.info(f"Is a command pending? {cls._did_we_send_a_command()}")
            # logger.info(f"Cmd sent: {cls.cmd_sent}")

            if not cls._did_we_send_a_command():  # Add timeout for retry
                # Check for telemetry
                if cls._now - cls._prev_tm_time > cls.telemetry_period and not cls._not_waiting_tm_response:
                    cls.request_telemetry()

            if not cls._did_we_send_a_command():  # Add timeout for retry
                if FileTransfer.in_progress:
                    # Check if we need to request the next file packet
                    if not cls.just_requested_file_packet:
                        cls.request_next_file_packet()

            # Check OD states
            # For now, just ping the OD status

            success = cls.receive_response()
            if not success:
                # Need to add to timeout / retry logic
                pass

            # Fault management
            # TODO

        elif cls.state == PayloadState.SHUTTING_DOWN:
            # Wait for the Payload to shutdown

            if cls.time_we_sent_shutdown + cls.TIMEOUT_SHUTDOWN < time.monotonic():
                # We have waited too long
                # Force the shutdown by cutting the power
                cls.turn_off_power()
                # Log and report error
                cls.last_error = ErrorCodes.TIMEOUT_SHUTDOWN

        elif cls.state == PayloadState.REBOOTING:
            # Wait for the Payload to reboot
            pass

    @classmethod
    def receive_response(cls):
        recv = cls.communication_interface.receive()
        print(recv)
        if recv:
            res = Decoder.decode(recv)
            cls.cmd_sent -= 1
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
                PayloadTM.print()
                cls._prev_tm_time = cls._now
                cls._not_waiting_tm_response = False
                return True

            elif sent_cmd_id == CommandID.REQUEST_IMAGE and resp == ErrorCodes.OK:
                # Start the file transfer
                FileTransfer.start_transfer(FileTransferType.IMAGE)
                logger.info("File transfer started.")
                cls.just_requested_file_packet = False
                return True

            elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.OK:
                # Continue the file transfer
                cls.just_requested_file_packet = False
                DH.log_image(Resp_RequestNextFilePacket.received_data)
                FileTransfer.ack_packet()  # increment the counter
                # if FileTransfer.packet_nb == 2:
                #    FileTransfer.packet_nb = 3129
                return True

            elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.NO_MORE_FILE_PACKET:
                cls.no_more_file_packet_to_receive = True
                FileTransfer.stop_transfer()
                DH.image_completed()
                logger.info("Completed image transfer. No more file packet to receive.")
                return True

            else:
                logger.error(f"Command error received: {resp}")  # TODO: map to good string for logging purposes
                cls.last_error = resp
                return False
        return False

    @classmethod
    def ping(cls):
        cls.communication_interface.send(Encoder.encode_ping())
        resp = cls.communication_interface.receive()
        if resp:  # a ping is immediate so if we don't receive a response, we assume it is not connected
            return Decoder.decode(resp) == _PING_RESP_VALUE
        return False

    @classmethod
    def shutdown(cls):
        # Simply send the shutdown command
        cls.communication_interface.send(Encoder.encode_shutdown())
        cls.cmd_sent += 1
        cls.state = PayloadState.SHUTTING_DOWN
        cls.time_we_sent_shutdown = time.monotonic()

    @classmethod
    def request_telemetry(cls):
        logger.info("Requesting telemetry...")
        cls.communication_interface.send(Encoder.encode_request_telemetry())
        cls.cmd_sent += 1
        cls._not_waiting_tm_response = True

    @classmethod
    def enable_cameras(cls):
        cls.communication_interface.send(Encoder.encode_enable_cameras())
        cls.cmd_sent += 1

    @classmethod
    def disable_cameras(cls):
        cls.communication_interface.send(Encoder.encode_disable_cameras())
        cls.cmd_sent += 1

    @classmethod
    def request_image_transfer(cls):
        # This starts the process for image transfer which will be executed in the background by the controller at each cycle
        if cls.state != PayloadState.READY:
            logger.error("Cannot request image transfer. Payload is not ready.")
            return False

        cls.communication_interface.send(Encoder.encode_request_image())
        cls.cmd_sent += 1
        cls.no_more_file_packet_to_receive = False
        return True

    @classmethod
    def request_next_file_packet(cls):
        if cls.state != PayloadState.READY:
            logger.error("Cannot request next file packet. Payload is not ready.")
            return False

        if not cls.just_requested_file_packet:
            cls.communication_interface.send(Encoder.encode_request_next_file_packet(FileTransfer.packet_nb))
            cls.cmd_sent += 1
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
        pass

    @classmethod
    def turn_off_power(cls):
        # This is an expensive and drastic operation on the HW so must be limited to strict necessity
        # Preferable after a shutdown command
        pass

    @classmethod
    def force_reboot(cls):
        # This is an expensive and drastic operation on the HW so must be limited to strict necessity
        # Preferable after a shutdown command
        pass
