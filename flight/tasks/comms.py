# Communication task which uses the radio to transmit and receive messages.
from apps.command import QUEUE_STATUS, CommandQueue
from apps.command.supervisor import CommandSupervisor
from apps.comms.comms import SATELLITE_RADIO
from apps.comms.fifo import TransmitQueue
from apps.comms.modes import COMMS_MODE
from apps.telemetry.middleware import Frame as TelemetryFrame  # this will substitute for the old telemetry packer
from apps.telemetry.splat.splat.telemetry_codec import Command, pack  # this should be implemented in middleware
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.dh_constants import COMMS_IDX
from core.scheduler import sleep
from core.states import STATES
from core.time_processor import TimeProcessor as TPM


class Task(TemplateTask):
    # Number of packets to transmit back-to-back before yielding to the
    # scheduler. Bigger -> higher TX throughput but longer scheduler blackout.
    # Bounded by HW watchdog timeout. Tune empirically.
    TX_BURST_SIZE = 15

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

        # Initialize log_data array for telemetry
        self.log_data = [0] * 11  # 11 COMMS variables

        SATELLITE_RADIO.restore_comms_mode_from_persistent_state()
        SATELLITE_RADIO.set_rx_mode()

    async def transmit_message(self):
        """
        Will transmit whatever is available on the transmit queue
        it should only be packets in bytes
        It will add to that packet the header (cs of the satellite)
        TODO: add tx timeout when more information about duty cycle is available
        """

        self.log_info("Checking transmit queue for packets to send...")
        self.log_info(f"  Transmit queue size: {TransmitQueue.get_size()}")

        if TransmitQueue.packet_available():
            self.update_comms_telemetry()  # will only update comms data when something is sent or received

        sent_in_burst = 0
        while TransmitQueue.packet_available():
            self.log_info("  Packet available in TransmitQueue, preparing for transmission")
            # If we have a packet to transmit, set it in the radio
            packet, queue_error_code = TransmitQueue.pop_packet()
            if queue_error_code == QUEUE_STATUS.OK:
                packed_packet = pack(packet, callsign=SATELLITE_RADIO.SC_CALLSIGN)   # changed and the entries in transmitqueue are no longer packed
                SATELLITE_RADIO.transmit_message(packed_packet)
            else:
                self.log_error("Error popping packet from TransmitQueue")
            sent_in_burst += 1
            if sent_in_burst >= self.TX_BURST_SIZE:
                # Yield to scheduler after a burst so watchdog (and other tasks)
                # get CPU time. Burst size bounded by HW watchdog timeout.
                await sleep(0)
                sent_in_burst = 0

    def receive_message(self):
        """
        Receive data from the radio. Currently it only receives commands from the GS
        records the rssi and adds the command to the command queue for processing by the command processor task.
        """

        self.log_info("Checking for incoming messages from GS...")
        if SATELLITE_RADIO.data_available():

            # Read packet present in the RX buffer
            message_object = SATELLITE_RADIO.receive_message()

            self.update_comms_telemetry()  # will only update comms data when something is sent or received

            if not isinstance(message_object, Command):
                self.log_warning("[COMMS ERROR] Received invalid command object from GS")
                return

            CommandQueue.overwrite_command(
                message_object
            )  # [TODO] - not sure why overwrite instead of push, i copied this from the old code

    def check_periodic_telemetry(self):
        """
        Checks if it's time to send periodic telemetry, and if so, prepares the telemetry report for downlink.
        """
        current_time = TPM.time()

        mode = SATELLITE_RADIO.get_comms_mode()
        if mode == COMMS_MODE.RF_STOP or CommandSupervisor.has_pending_action():
            return

        if current_time - self.last_periodic_telemetry_time >= self.periodic_telemetry_interval:
            # Time to send periodic telemetry
            self.log_info("Preparing periodic telemetry report for downlink")
            packet = self.periodic_telemetry_report()  # This calls the packing function implemented in the middleware
            TransmitQueue.push_packet(
                packet
            )  # push the packet to the transmit queue, where it will be sent in the next transmission window
            self.last_periodic_telemetry_time = current_time

    def update_comms_telemetry(self):
        """
        Update telemetry data from SATELLITE_RADIO counters and write to DataHandler.
        """
        # Populate telemetry data from SATELLITE_RADIO
        self.log_data[COMMS_IDX.RX_PACKET_COUNT] = SATELLITE_RADIO.rx_packet_count
        self.log_data[COMMS_IDX.RX_DIGIPEATER_COUNT] = SATELLITE_RADIO.rx_digipeater_count
        self.log_data[COMMS_IDX.TX_DIGIPEATER_COUNT] = SATELLITE_RADIO.tx_digipeater_count
        self.log_data[COMMS_IDX.FAILED_UNPACK_COUNT] = SATELLITE_RADIO.failed_unpack_count
        self.log_data[COMMS_IDX.CRC_ERROR_COUNT] = SATELLITE_RADIO.crc_error_count
        self.log_data[COMMS_IDX.UNDEF_ERROR_COUNT] = SATELLITE_RADIO.undef_error_count
        self.log_data[COMMS_IDX.PACKET_NONE_COUNT] = SATELLITE_RADIO.packet_none_count
        self.log_data[COMMS_IDX.PACKET_AUTH_FAIL_COUNT] = SATELLITE_RADIO.packet_auth_fail_count
        self.log_data[COMMS_IDX.TX_PACKET_COUNT] = SATELLITE_RADIO.tx_packet_count
        self.log_data[COMMS_IDX.TX_FAILED_COUNT] = SATELLITE_RADIO.tx_failed_count
        self.log_data[COMMS_IDX.RX_MESSAGE_RSSI] = SATELLITE_RADIO.rx_message_rssi

        # Log to DataHandler
        DH.log_data("comms", self.log_data)

    async def main_task(self):
        # Main comms task loop

        if SM.current_state == STATES.STARTUP:
            # No comms in STARTUP
            return

        # Register COMMS data process if it doesn't exist
        if not DH.data_process_exists("comms"):
            data_format = "HHHHHHHHHHe"
            DH.register_data_process("comms", data_format, True, data_limit=100000, write_interval=5)

        self.check_periodic_telemetry()  # check if it's time to send periodic telemetry
        await self.transmit_message()  # check if we have messages to transmit to GS
        self.receive_message()  # check if we have received messages from GS
        CommandSupervisor.process_pending_action()   # TODO - should be its own task. Keeping this way because of time constraints
