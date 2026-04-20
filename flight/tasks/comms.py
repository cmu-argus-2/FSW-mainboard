# Communication task: radio TX/RX and periodic telemetry.
from apps.command import QUEUE_STATUS, CommandQueue
from apps.command.supervisor import CommandSupervisor
from apps.comms.comms import SATELLITE_RADIO
from apps.comms.fifo import TransmitQueue
from apps.comms.modes import COMMS_MODE
from apps.telemetry.middleware import Frame as TelemetryFrame
from apps.telemetry.splat.splat.telemetry_codec import Command, pack
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from core.time_processor import TimeProcessor as TPM


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)

        self.name = "COMMS"

        self.periodic_telemetry_interval = SATELLITE_RADIO.HB_PERIOD
        self.periodic_telemetry_report = TelemetryFrame.pack_tm_heartbeat
        self.last_periodic_telemetry_time = TPM.time()

        SATELLITE_RADIO.restore_comms_mode_from_persistent_state()
        SATELLITE_RADIO.set_rx_mode()

    def transmit_message(self):
        """Drain the transmit queue and send each packet over the radio."""
        self.log_info("Checking transmit queue for packets to send...")
        self.log_info(f"  Transmit queue size: {TransmitQueue.get_size()}")

        while TransmitQueue.packet_available():
            self.log_info("  Packet available in TransmitQueue, preparing for transmission")
            packet, queue_error_code = TransmitQueue.pop_packet()
            if queue_error_code == QUEUE_STATUS.OK:
                packed_packet = pack(packet, callsign=SATELLITE_RADIO.SC_CALLSIGN)
                self.log_info(f"Set packet for transmission: {packed_packet}")
                SATELLITE_RADIO.transmit_message(packed_packet)
            else:
                self.log_error("Error popping packet from TransmitQueue")

    def receive_message(self):
        """Receive commands from the ground station and enqueue for processing."""
        self.log_info("Checking for incoming messages from GS...")
        if SATELLITE_RADIO.data_available():
            message_object = SATELLITE_RADIO.receive_message()
            if not isinstance(message_object, Command):
                self.log_warning("[COMMS ERROR] Received invalid command object from GS")
                return

            self.log_info(f"Received command from GS: {message_object}")
            CommandQueue.overwrite_command(message_object)
            DH.log_data("comms", [TPM.time(), SATELLITE_RADIO.get_rssi()])

    def check_periodic_telemetry(self):
        """Send periodic telemetry if the interval has elapsed."""
        current_time = TPM.time()
        mode = SATELLITE_RADIO.get_comms_mode()

        if mode == COMMS_MODE.RF_STOP or CommandSupervisor.has_pending_action():
            return

        if current_time - self.last_periodic_telemetry_time >= self.periodic_telemetry_interval:
            self.log_info("Preparing periodic telemetry report for downlink")
            packet = self.periodic_telemetry_report()
            TransmitQueue.push_packet(packet)
            self.last_periodic_telemetry_time = current_time

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            return

        self.check_periodic_telemetry()
        self.transmit_message()
        CommandSupervisor.process_pending_action()   # TODO - should be its own task. Keeping this way because of time constraints
        self.receive_message()
