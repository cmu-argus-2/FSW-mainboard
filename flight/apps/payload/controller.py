"""
Payload Control Interface

This module defines the Payload Controller class, which is responsible for managing the main interface between
the host and the Payload.

Author: Ibrahima Sory Sow

"""

import time

from definitions import CommandID, ErrorCodes
from protocol import Decoder, Encoder

_PING_RESP_VALUE = 0x60


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

    @classmethod
    def initialize(cls, communication_interface):
        cls.communication_interface = communication_interface
        cls.communication_interface.connect()

    @classmethod
    def deinitialize(cls):
        cls.communication_interface.disconnect()

    @classmethod
    def did_we_send_a_command(cls):
        return len(cls.last_cmds_sent) > 0

    @classmethod
    def process_external_requests(cls):
        pass

    @classmethod
    def run_control_logic(cls):
        # Move this potentially at the task level

        if cls.state == PayloadState.OFF:
            # Do nothing unless it's time to power on
            pass

        elif cls.state == PayloadState.POWERING_ON:
            # Wait for the Payload to be ready

            # The serial link will be purged by the payload when it opens its channel
            # so we ping to check until it is ready, i.e. the ping response is received
            pass

        elif cls.state == PayloadState.READY:
            # Check for commands
            pass

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
