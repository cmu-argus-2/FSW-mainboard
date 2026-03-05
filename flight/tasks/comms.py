# Communication task which uses the radio to transmit and receive messages.
from apps.command import QUEUE_STATUS, CommandQueue
from apps.comms.comms import SATELLITE_RADIO
from apps.comms.fifo import TransmitQueue
from apps.telemetry.middleware import Frame as TelemetryFrame  # this will substitute for the old telemetry packer

# from apps.telemetry import TelemetryPacker
from apps.telemetry.splat.splat.telemetry_codec import Command, pack  # this should be implemented in middleware
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from core.time_processor import TimeProcessor as TPM


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)

        self.name = "COMMS"

        # variables for handling periodic telemetry
        self.periodic_telemetry_interval = (
            SATELLITE_RADIO.HB_PERIOD
        )  # amount of seconds between periodic telemetry downlink [check] - this should be a config
        self.periodic_telemetry_report = (
            TelemetryFrame.pack_tm_heartbeat
        )  # the packing function of the report to be downlinked periodically
        self.last_periodic_telemetry_time = TPM.time()  # timestamp of the last periodic telemetry downlink

        SATELLITE_RADIO.set_rx_mode()

    def transmit_message(self):
        """
        Will transmit whatever is available on the transmit queue
        it should only be packets in bytes
        It will add to that packet the header (cs of the satellite)
        TODO: add tx timeout when more information about duty cycle is available
        """

        self.log_info("Checking transmit queue for packets to send...")
        self.log_info(f"  Transmit queue size: {TransmitQueue.get_size()}")

        while TransmitQueue.packet_available():
            self.log_info("  Packet available in TransmitQueue, preparing for transmission")
            # If we have a packet to transmit, set it in the radio
            packet, queue_error_code = TransmitQueue.pop_packet()
            if queue_error_code == QUEUE_STATUS.OK:
                packed_packet = pack(packet, callsign=SATELLITE_RADIO.SC_CALLSIGN)   # changed and the entries in transmitqueue are no longer packed
                self.log_info(f"Set packet for transmission: {packed_packet}")
                SATELLITE_RADIO.transmit_message(packed_packet)
            else:
                self.log_error("Error popping packet from TransmitQueue")

    def receive_message(self):
        """
        Receive data from the radio. Currently it only receives commands from the GS
        records the rssi and adds the command to the command queue for processing by the command processor task.
        """

        self.log_info("Checking for incoming messages from GS...")
        if SATELLITE_RADIO.data_available():

            # Read packet present in the RX buffer
            message_object = SATELLITE_RADIO.receive_message()

            if not isinstance(message_object, Command):
                self.log_warning("[COMMS ERROR] Received invalid command object from GS")
                return
            self.log_info(f"Received command from GS: {message_object}")

            CommandQueue.overwrite_command(
                message_object
            )  # [TODO] - not sure why overwrite instead of push, i copied this from the old code

            DH.log_data("comms", [TPM.time(), SATELLITE_RADIO.get_rssi()])

    def check_periodic_telemetry(self):
        """
        Checks if it's time to send periodic telemetry, and if so, prepares the telemetry report for downlink.
        """
        current_time = TPM.time()

        if current_time - self.last_periodic_telemetry_time >= self.periodic_telemetry_interval:
            # Time to send periodic telemetry
            self.log_info("Preparing periodic telemetry report for downlink")
            packet = self.periodic_telemetry_report()  # This calls the packing function implemented in the middleware
            TransmitQueue.push_packet(
                packet
            )  # push the packet to the transmit queue, where it will be sent in the next transmission window
            self.last_periodic_telemetry_time = current_time

    async def main_task(self):
        # Main comms task loop

        if SM.current_state == STATES.STARTUP:
            # No comms in STARTUP
            return

        self.check_periodic_telemetry()  # check if it's time to send periodic telemetry
        self.transmit_message()  # check if we have messages to transmit to GS
        self.receive_message()  # check if we have received messages from GS
