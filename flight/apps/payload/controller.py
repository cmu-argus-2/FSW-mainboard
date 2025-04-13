"""
Payload Control Interface

This module defines the Payload Controller class, which is responsible for managing the main interface between
the host and the Payload.

Author: Ibrahima Sory Sow

"""

import time

from definitions import CommandID, ErrorCodes, ExternalRequest, FileTransfer, FileTransferType, PayloadTM
from protocol import Decoder, Encoder

_PING_RESP_VALUE = 0x60
_TELEMETRY_FREQUENCY = 0.2  # seconds


class PayloadState:  # Only from the host perspective
    OFF = 0  # Fully powered down
    POWERING_ON = 1  # Power and boot sequence started
    READY = 2  # Fully operational
    SHUTTING_DOWN = 3  # Graceful shutdown in progress
    REBOOTING = 4  # Going through shutdown + boot


class PayloadController:

    # Bi-directional communication interface
    communication_interface = None

    # State of the Payload from the host perspective
    state = PayloadState.OFF

    # Last error (from the host perspective)
    last_error = None

    # Contains the last command IDs sent to the Payload
    last_cmds_sent = []

    # No response counter
    no_resp_counter = 0

    # Timeout for the shutdown process
    TIMEOUT_SHUTDOWN = 10  # 10 seconds
    time_we_sent_shutdown = 0

    # Current request
    current_request = ExternalRequest.NO_ACTION
    timestamp_request = 0

    # Last telemetry received
    _prev_tm_time = time.monotonic()
    _now = time.monotonic()
    telemetry_period = 1 / _TELEMETRY_FREQUENCY  # seconds

    @classmethod
    def initialize(cls, communication_interface):
        cls.communication_interface = communication_interface
        cls.communication_interface.connect()

    @classmethod
    def deinitialize(cls):
        cls.communication_interface.disconnect()

    @classmethod
    def _did_we_send_a_command(cls):
        return len(cls.last_cmds_sent) > 0

    @classmethod
    def add_request(cls, request: ExternalRequest) -> bool:
        if not isinstance(request, int) or request < ExternalRequest.NO_ACTION or request >= ExternalRequest.INVALID:
            # Invalid request
            # log error
            return False
        cls.current_request = request
        cls.timestamp_request = time.monotonic()

    @classmethod
    def process_external_requests(cls):
        if cls.current_request != ExternalRequest.NO_ACTION:
            # Process the request
            # switch case TODO
            pass

    @classmethod
    def _switch_to_state(cls, new_state: PayloadState):
        if new_state != cls.state:
            # Log state change
            cls.state = new_state

    @classmethod
    def run_control_logic(cls):
        # Move this potentially at the task level
        cls._now = time.monotonic()

        if cls.state == PayloadState.OFF:
            # Do nothing unless it's time to power on
            pass

        elif cls.state == PayloadState.POWERING_ON:
            # Wait for the Payload to be ready

            # The serial link will be purged by the payload when it opens its channel
            # so we ping to check until it is ready, i.e. the ping response is received
            pass

        elif cls.state == PayloadState.READY:

            # Check for requests
            cls.process_external_requests()

            # Check for telemetry
            if cls._now - cls._prev_tm_time > cls.telemetry_period:
                # Request telemetry
                cls.request_telemetry()

                resp = cls.receive_response()
                if resp:
                    # print("[INFO] Telemetry received.")
                    PayloadTM.print()
                    cls._prev_tm_time = cls._now

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
        resp = cls.communication_interface.receive()
        if resp:
            return Decoder.decode(resp)
        return ErrorCodes.NO_RESPONSE

    @classmethod
    def ping(cls):
        cls.communication_interface.send(Encoder.encode_ping())

        resp = cls.communication_interface.receive()
        if resp:
            return Decoder.decode(resp) == _PING_RESP_VALUE
        return False

    @classmethod
    def shutdown(cls):
        # Simply send the shutdown command
        cls.communication_interface.send(Encoder.encode_shutdown())
        cls.state = PayloadState.SHUTTING_DOWN
        cls.time_we_sent_shutdown = time.monotonic()

    @classmethod
    def request_telemetry(cls):
        cls.communication_interface.send(Encoder.encode_request_telemetry())

    @classmethod
    def enable_cameras(cls):
        cls.communication_interface.send(Encoder.encode_enable_cameras())

    @classmethod
    def disable_cameras(cls):
        cls.communication_interface.send(Encoder.encode_disable_cameras())

    @classmethod
    def request_image_transfer(cls):
        # This starts the process for image transfer which will be executed in the background by the controller at each cycle
        cls.communication_interface.send(Encoder.encode_request_image())

    @classmethod
    def _file_transfer_logic(cls):
        if FileTransfer.in_progress:

            cls.communication_interface.send(Encoder.encode_request_next_file_packet(FileTransfer.packet_nb))
            resp = cls.communication_interface.receive()
            if resp:
                # Decode the response
                decoded_resp = Decoder.decode(resp)
                if decoded_resp:  # all good
                    # grab the data and store
                    FileTransfer.ack_packet()  # increment the counter
                    pass
                else:  # Error
                    pass

    @classmethod
    def turn_on_power(cls):
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
