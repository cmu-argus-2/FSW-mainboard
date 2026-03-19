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
    Resp_RequestNextFilePackets,
)
from apps.payload.protocol import Decoder, Encoder
from apps.payload.uart_comms import PayloadUART as PU
from core import DataHandler as DH
from core import logger
from core.dh_constants import PAYLOAD_IDX
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE

from apps.telemetry.splat.splat.telemetry_codec import Command, pack, unpack, Ack, Fragment, Report
from apps.telemetry.splat.splat.transport_layer import Transaction
from apps.payload.download_manager import DownloadManager

from micropython import const

_PING_RESP_VALUE = const(0x60)  # DO NOT CHANGE THIS VALUE


class PayloadState: 

    IDLE = 0   
    WATCHING = 1
    BOOTING = 2
    ACTIVE = 3
    PROCESSING = 4
    FINISHED = 5
    DOWNLOAD = 6
    OFF = 7
    FAIL = 8


def map_state(state):
    """
    Maps the string representation of the state to the actual state
    """
    if state == "IDLE":
        return PayloadState.IDLE
    if state == "WATCHING":
        return PayloadState.WATCHING
    if state == "BOOTING":
        return PayloadState.BOOTING
    if state == "ACTIVE":
        return PayloadState.ACTIVE
    if state == "PROCESSING":
        return PayloadState.PROCESSING
    if state == "FINISHED":
        return PayloadState.FINISHED
    if state == "DOWNLOAD":
        return PayloadState.DOWNLOAD
    if state == "OFF":
        return PayloadState.OFF
    if state == "FAIL":
        return PayloadState.FAIL
    raise ValueError(f"Invalid state: {state}")


class PayloadController:
    
    
    # State of the Payload from the host perspective
    current_state = PayloadState.IDLE
    command_list = []         # this is the list that will contain all the commands. this list will be ordered by timestamp
    current_command = None    # this is the command that is being executed at the moment
    
    
    # Time variables for diferente things
    BOOT_TS = 0        # time at which switched to booting state
    BOOT_TIMEOUT = 60  # how long it will wait for jetson to respond ping
    
    PROC_TS = 0        # time at which switched to processing state
    PROC_TIMEOUT = 60  # max amounts of seconds to run the experiment
    
    TELEM_TS = 0       # time at which last telemetry was requested
    TELEM_PERIOD = 30  # request telemetry every 30s
    
    OFF_TS = 0         # time at which switched to turning off state
    OFF_TIMEOUT = 20   # time to wait for the jetson to respond to shutdown command befoer forcing shutdown

    # Lets init uart connection.
    # TODO should this only be made once the jetson has been turned on?
    PU.connect()
    
    # flags used to process commands and ack
    received_experiment_ack = False
    received_ping_ack = False
    received_off_ack = False
    received_experiment_finished = False
    received_all_files_sent = False

    # Bi-directional communication interface
    communication_interface = None
    _interface_injected = False



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
    payload_tm_data_format = "QQQ" + 15 * "B" + "H" + 2 * "B" + 3 * "H"
    log_data = [0] * len(payload_tm_data_format)
    _prev_tm_time = TPM.monotonic()
    _now = TPM.monotonic()
    telemetry_period = const(10)  # seconds
    _not_waiting_tm_response = False

    # File transfer
    no_more_file_packet_to_receive = False
    just_requested_file_packet = False

    # Batch transfer settings
    USE_BATCH_TRANSFER = True  # Enable batch requests
    BATCH_SIZE = 25  # Request 25 packets at a time

    _BITS_PER_BYTE = 10  # 1 start, 8 data, 1 stop (8N1)

    if SATELLITE.PAYLOADUART_BAUDRATE is not None:
        _TX_TIME = PU._DATA_PACKET_SIZE * _BITS_PER_BYTE / SATELLITE.PAYLOADUART_BAUDRATE
    else:
        _TX_TIME = 0.01  # TODO: Default to 10ms if baudrate not set for now

    _PROCESSING_SLACK = 0.001
    _EST_PKT_TX_TIME = _TX_TIME + _PROCESSING_SLACK

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
    
    # this is the dict were the transactions will be stored
    # TODO - will probably only have one transaction at a time, might not be worth having a dict
    transaction_dict = {} 
    received_create_trans = False
    received_init_trans = False

    # Download manager for handling file transfers
    download_manager = DownloadManager()

    
    @classmethod
    def switch_state(cls, state):
        """
        state will be a string
        It will change the current state to the desired state, and run whatever functions necessary to start that state
        """
        logger.info(f"[PAYLOAD] - Switching from {cls.current_state} to {state}")
        cls.current_state = map_state(state)
        
        # booting state needs to turn on the satellite
        if cls.current_state == PayloadState.BOOTING:
            logger.info("[PAYLOAD] -  Turning on jetson")
            cls.turn_on_power()
            
        # active state, need to get the desired command
        if cls.current_state == PayloadState.ACTIVE:
            cls.current_command = cls.get_first_command()
            cls.remove_first_command()    
            logger.info(f"[PAYLOAD] -  Selected command: {cls.current_command}")

        if cls.current_state == PayloadState.DOWNLOAD:
            cls.received_all_files_sent = False
        
        # turn off state needs to send turn off command
        if cls.current_state == PayloadState.OFF:
            logger.info("[PAYLOAD] -  Sending turn off command")
            cls.send_turn_off_command()
            
    @classmethod
    def add_command(cls, ts, camera_bit_flag, level_of_processing, width, height):
        """
        Given the information it will create the command and add it to the list
        it should add ordered by timestamp
        the command_list will be a list of lists. The inside list will contain the necessary info
            ts, camera_bit_flag, level_of_processing, width, height 
        """
        
        # check the limits on the camera bit flag
        if camera_bit_flag < 0 or camera_bit_flag > 15:
            logger.error(f"[PAYLOAD] - Invalid camera bit flag: {camera_bit_flag}")
            return False
        
        if ts != 0 and ts < TPM.time():
            logger.error(f"[PAYLOAD] - Timestamp in the past: {ts}")
            return False
        
        # TODO - add limit to resolution and level of processing

        # need to add the data in the corerct spot in the list
        # it has to be ordered by timestamp
        cls.command_list.append((ts, camera_bit_flag, level_of_processing, width, height))
        cls.command_list.sort(key=lambda x: x[0])  # Sort by timestamp
        
        logger.info(f"[PAYLOAD] - Command added: {ts}, {camera_bit_flag}, {level_of_processing}, {width}, {height}")
        
        return True

    @classmethod
    def command_available(cls):
        """
        Return true if there is one or more command in the list
        false otherwise
        """
        return len(cls.command_list) > 0
    
    @classmethod
    def get_first_command(cls):
        """
        Returns the first command in the list
        """
        return cls.command_list[0]
    
    @classmethod
    def remove_first_command(cls):
        """
        Will delete the first command from the command list
        """
        cls.command_list.pop(0)
        
        
    @classmethod
    def read(cls, bytes):
        return PU.read(bytes)
        
    
    @classmethod
    def send_ping(cls):
        """
        This should send a ping to uart
        """
        
        # 1. create the ping command
        command = Command("PING")
        command.add_argument("ts", TPM.time())
        logger.info("[PAYLOAD] - Sending ping command")
        # 2. send to uart
        PU.send(pack(command))
        
    @classmethod
    def send_confirm_last_batch(cls, command):
        """
        This should send a confirm last batch command to uart
        """
        logger.info("[PAYLOAD] - Sending confirm last batch command")
        PU.send(pack(command))

    @classmethod
    def send_current_command(cls):
        """
        Will send the current command to the jetson
        """
        
        logger.info(f"[PAYLOAD] - Sending current command {cls.current_command}")
        
        # 1. create the command
        command = Command("EXPERIMENT")
        
        # 2. set the arguments
        command.set_arguments(*cls.current_command)
        logger.info(f"[PAYLOAD] - Command: {command} args: {command.arguments}")
        
        # 3. pack the command and send to uart
        PU.send(pack(command))
        
    @classmethod
    def send_telemetry_command(cls):
        """
        Will send a command requestin the telemetry command
        """
        
        # 1. create the command
        command = Command("REQUEST_TM_PAYLOAD")
        
        # 3. send the command
        PU.send(pack(command))
        
        logger.info("[PAYLOAD] - Sent tm request.")
    
    @classmethod
    def send_create_trans(cls, tid, string_command):
        """
        tid is going to be the transaction id
        string command will be the path of the file
        
        now sure how I will implement the logic for this. Probably using the payload task in download mode
        but for now I will just forward the commands from the groundstation here for testing
        """
        
        # create the command
        command = Command("CREATE_TRANS")
        command.add_argument("tid", tid)
        command.add_argument("string_command", string_command)
        
        # create the transaction in the transaction manager
               
        # send the command
        PU.send(pack(command))
        logger.info(f"[PAYLOAD] - Sent create transaction command: {tid}, {string_command}")
        
    @classmethod
    def send_turn_off_command(cls):
        """
        Will send the command to turn off the jetson
        """
        logger.error("Please implement me")
        
    @classmethod 
    def process_uart(cls):
        """
        This function will read from uart and try and process the commands/ack received
        """
        
        data = cls.read(255)   # read the max packet size
        
        if not data:
            # nothing to be done here
            return False

        logger.info(f"[PAYLOAD] - Received data from uart: {data[0:10]}")
        
        # try and unpack the data
        callsign, message_object = unpack(data)
        
        if isinstance(message_object, Ack):
            logger.info(f"[PAYLOAD] -   Received ack: {message_object}")
            cls.process_ack(message_object)
        if isinstance(message_object, Command):
            cls.process_command(message_object)
            logger.info(f"[PAYLOAD] -   Received command: {message_object}")
        if isinstance(message_object, Fragment):
            cls.process_fragment(message_object)
        if isinstance(message_object, Report):
            cls.process_report(message_object)
            
    @classmethod
    def process_report(cls, report):
        """
        This function will process the report message
        """
        logger.info(f"[PAYLOAD] - Processing report: {report}")
        
        if report.name == "TM_PAYLOAD":
            cls.process_tm_payload_report(report)
            
    @classmethod 
    def process_tm_payload_report(cls, report):
        """
        Process telemetry payload report and log to DataHandler.
        Maps TM_PAYLOAD variables to PAYLOAD_IDX and adds controller metadata.
        """
        logger.info(f"[PAYLOAD] - Processing TM_PAYLOAD report: {report}")

        # reports.variables is a dict, each entry is the subsystem and the value is another dict
        # that has the variable names as keys and their values as values
        
        if not DH.data_process_exists("payload_tm"):
            logger.error("[PAYLOAD] - Data process 'payload_tm' does not exist")
            return
        
        for ss, var_dict in report.variables.items():
            logger.info(f"[PAYLOAD] - Processing subsystem: {ss}")

            for var_name, value in var_dict.items():
                logger.info(f"[PAYLOAD] -   {var_name}: {value}")
        
        cls.log_data[PAYLOAD_IDX.SYSTEM_TIME] = report.variables["PAYLOAD_TM"]["SYSTEM_TIME"]
        cls.log_data[PAYLOAD_IDX.SYSTEM_UPTIME] = report.variables["PAYLOAD_TM"]["SYSTEM_UPTIME"]
        cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_TIME] = report.variables["PAYLOAD_TM"]["LAST_EXECUTED_CMD_TIME"]
        cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_ID] = report.variables["PAYLOAD_TM"]["LAST_EXECUTED_CMD_ID"]
        cls.log_data[PAYLOAD_IDX.PD_STATE_MAINBOARD] = report.variables["PAYLOAD_TM"]["PD_STATE_MAINBOARD"]
        cls.log_data[PAYLOAD_IDX.PD_STATE_JETSON] = report.variables["PAYLOAD_TM"]["PD_STATE_JETSON"]
        cls.log_data[PAYLOAD_IDX.LATEST_ERROR] = report.variables["PAYLOAD_TM"]["LATEST_ERROR"]
        cls.log_data[PAYLOAD_IDX.DISK_USAGE] = report.variables["PAYLOAD_TM"]["DISK_USAGE"]
        cls.log_data[PAYLOAD_IDX.RAM_USAGE] = report.variables["PAYLOAD_TM"]["RAM_USAGE"]
        cls.log_data[PAYLOAD_IDX.SWAP_USAGE] = report.variables["PAYLOAD_TM"]["SWAP_USAGE"]
        cls.log_data[PAYLOAD_IDX.ACTIVE_CORES] = report.variables["PAYLOAD_TM"]["ACTIVE_CORES"]
        cls.log_data[PAYLOAD_IDX.CPU_LOAD_0] = report.variables["PAYLOAD_TM"]["CPU_LOAD_0"]
        cls.log_data[PAYLOAD_IDX.CPU_LOAD_1] = report.variables["PAYLOAD_TM"]["CPU_LOAD_1"]
        cls.log_data[PAYLOAD_IDX.CPU_LOAD_2] = report.variables["PAYLOAD_TM"]["CPU_LOAD_2"]
        cls.log_data[PAYLOAD_IDX.CPU_LOAD_3] = report.variables["PAYLOAD_TM"]["CPU_LOAD_3"]
        cls.log_data[PAYLOAD_IDX.CPU_LOAD_4] = report.variables["PAYLOAD_TM"]["CPU_LOAD_4"]
        cls.log_data[PAYLOAD_IDX.CPU_LOAD_5] = report.variables["PAYLOAD_TM"]["CPU_LOAD_5"]
        cls.log_data[PAYLOAD_IDX.TEGRASTATS_PROCESS_STATUS] = report.variables["PAYLOAD_TM"]["TEGRASTATS_PROCESS_STATUS"]
        cls.log_data[PAYLOAD_IDX.GPU_FREQ] = report.variables["PAYLOAD_TM"]["GPU_FREQ"]
        cls.log_data[PAYLOAD_IDX.CPU_TEMP] = report.variables["PAYLOAD_TM"]["CPU_TEMP"]
        cls.log_data[PAYLOAD_IDX.GPU_TEMP] = report.variables["PAYLOAD_TM"]["GPU_TEMP"]
        cls.log_data[PAYLOAD_IDX.VDD_IN] = report.variables["PAYLOAD_TM"]["VDD_IN"]
        cls.log_data[PAYLOAD_IDX.VDD_CPU_GPU_CV] = report.variables["PAYLOAD_TM"]["VDD_CPU_GPU_CV"]
        cls.log_data[PAYLOAD_IDX.VDD_SOC] = report.variables["PAYLOAD_TM"]["VDD_SOC"]
        DH.log_data("payload_tm", cls.log_data)
        
    @classmethod
    def process_ack(cls, ack):
        """
        It will check the ack command id and set the corresponding variable to true
        TODO - remove hard code command id
        """
        logger.info(f"[PAYLOAD] - Processing ack: {ack}")
        # see if it was a ping ack
        if ack.cmd_id == 28:
            # it was a ping command
            if cls.received_ping_ack == True:
                logger.error("[PAYLOAD] - PING ACK OVERRIDDEN")
            cls.received_ping_ack = True
            logger.info("[PAYLOAD] - received_ping_ack set to true")
            return
            
        # see if it was a experiment ack
        if ack.cmd_id == 27:
            # it was a experiment command
            if cls.received_experiment_ack == True:
                logger.error("[PAYLOAD] - EXPERIMENT ACK OVERRIDDEN")
            cls.received_experiment_ack = True
            return
    
        # see if it was a off ack
        if ack.cmd_id == 26:
            # it was a off command
            if cls.received_off_ack == True:
                logger.error("[PAYLOAD] - OFF ACK OVERRIDDEN")
            cls.received_off_ack = True
            return
        
    @classmethod
    def process_init_trans(cls, command):
        """
        This function will process the initialization of a transaction
        """
        tid = command.arguments.get("tid", None)
        number_of_packets = command.arguments.get("number_of_packets", None)

        if tid is None or number_of_packets is None:
            logger.error(f"[PAYLOAD] - Invalid init transaction command: {tid}, {number_of_packets}")
            return False
        
        cls.transaction_dict[tid].number_of_packets = number_of_packets
        # MEMORY NOTE: Use set_number_packets() which initializes bitset instead of large list allocation
        cls.transaction_dict[tid].set_number_packets(number_of_packets)
        cls.add_transaction_for_download(tid, cls.transaction_dict[tid])
        
        

        logger.info(f"[PAYLOAD] - Processing init transaction command: {tid}, {number_of_packets}")
        return True
    
    @classmethod
    def process_create_trans(cls, command):
        """
        This function will process the creation of a transaction
        the controller will be the one dealing with the transaction between the satellite and the jetson
        """
        tid = command.arguments.get("tid", None)
        filename = command.arguments.get("string_command", None)

        if tid is None or filename is None:
            logger.error(f"[PAYLOAD] - Invalid create transaction command: {tid}, {filename}")
            return False
        
        filename = filename.rstrip("\x00")
        
        # need to give a random number for number_of_packets
        cls.transaction_dict[tid] = Transaction(tid, filename, number_of_packets=-1)

        logger.info(f"[PAYLOAD] - Processing create transaction command: {tid}, {filename}")
        return True
    
    @classmethod
    def process_command(cls, command):
        """
        It will check the commands that have been received a process them accordingly
        """
        
        # check experiment finished command (during PROCESSING)
        if command.name == "EXPERIMENT_FINISHED":
            if cls.received_experiment_finished == True:
                logger.error("[PAYLOAD] - EXPERIMENT FINISHED COMMAND OVERRIDDEN")
            cls.received_experiment_finished = True
        
        # check all files sent command (during DOWNLOAD)
        if command.name == "DOWNLOAD_FINISH":
            if cls.received_all_files_sent == True:
                logger.error("[PAYLOAD] - ALL FILES SENT COMMAND OVERRIDDEN")
            cls.received_all_files_sent = True
        
        # check for create trans command
        if command.name == "CREATE_TRANS":
            logger.info(f"[PAYLOAD] - Processing create transaction command: {command}")
            cls.received_create_trans = cls.process_create_trans(command)
            
        # check for init trans command
        if command.name == "INIT_TRANS":
            logger.info(f"[PAYLOAD] - Processing init transaction command: {command}")
            cls.received_init_trans = cls.process_init_trans(command)
            
        # generate ack and send to jetson
        ack = Ack(0, command.command_id)
        PU.send(pack(ack))

    @classmethod
    def process_fragment(cls, fragment):
        """
        This funciton will process the received fragments
        ideally this will only happen when in listening mode (triggered when the payload goes into download mode)
        """
        logger.info(f"[PAYLOAD] - Processing fragment: {fragment}")
        cls.download_manager.note_fragment_received(fragment)
        cls.transaction_dict[fragment.tid ].add_fragment(fragment)
        
    @classmethod
    def add_transaction_for_download(cls, tid, transaction):
        """
        Queue a transaction for download via the download manager.
        
        Args:
            tid: Transaction ID
            transaction: Transaction object
        """
        cls.download_manager.add_transaction(tid, transaction)
    
    @classmethod
    def get_download_status(cls):
        """
        Get current download status from the download manager.
        
        Returns:
            Dictionary with status information
        """
        return cls.download_manager.get_status()

    @classmethod
    def turn_on_power(cls):
        """
        This should turn on power to the jetson
        """
        logger.error("[PAYLOAD] - Turning on power to jetson, please implement this method")
    
    @classmethod
    def turn_off_power(cls):
        """
        This should turn off power to the jetson
        """
        logger.error("[PAYLOAD] - Turning off power to jetson, please implement this method")



    # @classmethod
    # def load_communication_interface(cls):
    #     # This function is called from the HAL to load the communication interface
    #     # This is done only once at startup
    #     if cls._interface_injected:
    #         logger.info("Communication interface already injected. Skipping injection.")
    #         return

    #     # Using build flag
    #     # if SATELLITE.BUILD == "FLIGHT":
    #     from apps.payload.uart_comms import PayloadUART

    #     cls.communication_interface = PayloadUART
    #     cls._interface_injected = True
    #     logger.info("Payload UART communication interface injected.")

    #     # elif SATELLITE.BUILD == "SIL":
    #     #     from apps.payload.ipc_comms import PayloadIPC

    #     #     cls.communication_interface = PayloadIPC
    #     #     cls._interface_injected = True
    #     #     logger.info("Payload IPC communication interface injected.")

    #     assert cls.communication_interface is not None, "Communication interface not injected. Cannot initialize controller."

    # @classmethod
    # def initialize(cls):
    #     if cls._interface_injected:
    #         return cls.communication_interface.connect()
    #     else:
    #         logger.error("Communication interface not injected yet.")
    #         return False

    # @classmethod
    # def deinitialize(cls):
    #     cls.communication_interface.disconnect()

    # @classmethod
    # def interface_injected(cls):
    #     return cls._interface_injected

    # @classmethod
    # def _did_we_send_a_command(cls):
    #     # TODO: add logic for retry here
    #     return cls.cmd_sent > 0

    # @classmethod
    # def add_request(cls, request: ExternalRequest) -> bool:
    #     if not isinstance(request, int) or request < ExternalRequest.NO_ACTION or request >= ExternalRequest.INVALID:
    #         # Invalid request
    #         logger.error(f"Invalid request: {request}")
    #         # TODO: add if a request is already being processed
    #         return False
    #     cls.current_request = request
    #     cls.timestamp_request = TPM.monotonic()
    #     return True

    # @classmethod
    # def _clear_request(cls):
    #     cls.current_request = ExternalRequest.NO_ACTION
    #     cls.timestamp_request = 0

    # @classmethod
    # def cancel_current_request(cls):
    #     if cls.state != PayloadState.READY:
    #         cls._clear_request()
    #         # TODO: need to add a specific logic to cancel the request
    #         # This should be used only when the payload is is not READY.
    #         # If in READY, it would have already been executing the request
    #         return True
    #     else:
    #         # Log
    #         return False

    # @classmethod
    # def handle_external_requests(cls):

    #     if cls.current_request == ExternalRequest.NO_ACTION:
    #         pass

    #     elif cls.current_request == ExternalRequest.TURN_ON:
    #         cls._switch_to_state(PayloadState.POWERING_ON)
    #         cls._clear_request()

    #     elif cls.current_request == ExternalRequest.TURN_OFF:
    #         cls._switch_to_state(PayloadState.SHUTTING_DOWN)
    #         cls.shutdown()
    #         cls._clear_request()

    #     elif cls.current_request == ExternalRequest.REBOOT:
    #         logger.info("Rebooting the Payload...")
    #         cls.attempting_reboot = True
    #         cls.shutdown()
    #         cls._switch_to_state(PayloadState.SHUTTING_DOWN)
    #         cls._clear_request()

    #     elif cls.current_request == ExternalRequest.CLEAR_STORAGE:
    #         # coming soon, after payload updates
    #         pass

    #     elif cls.current_request == ExternalRequest.REQUEST_IMAGE:
    #         logger.info("An image has been requested...")
    #         if cls.file_transfer_in_progress():
    #             logger.error("File transfer already in progress. Cannot request image.")
    #             return

    #         if not DH.file_process_exists("img"):
    #             logger.error("Image file process not found. Cannot request image.")
    #             return

    #         cls.request_image_transfer()
    #         cls._clear_request()

    #     elif cls.current_request == ExternalRequest.FORCE_POWER_OFF:
    #         # This is a last resort
    #         cls.turn_off_power()
    #         cls._switch_to_state(PayloadState.OFF)
    #         cls._clear_request()

    # @classmethod
    # def _switch_to_state(cls, new_state: PayloadState):
    #     if new_state != cls.state:
    #         cls.state = new_state
    #         logger.info(f"[PAYLOAD] Switching to state {map_state(new_state)}...")
    #         if new_state == PayloadState.READY:
    #             # clearing variables
    #             cls.must_re_attempt_boot = False
    #             cls.attempting_reboot = False
    #             cls.time_we_started_booting = 0
    #             cls.payload_sw_has_shutdown = False

    # @classmethod
    # def run_control_logic(cls):
    #     # Move this potentially at the task level
    #     cls._now = TPM.monotonic()

    #     # Check for requests
    #     cls.handle_external_requests()

    #     if cls.state == PayloadState.OFF:
    #         # Do nothing
    #         # Make sure the power line is off
    #         cls.turn_off_power()

    #         if cls.must_re_attempt_boot:
    #             # We have timed out while booting
    #             # Log error and reset the state
    #             logger.error("Timeout booting. Resetting state.")
    #             cls._switch_to_staate(PayloadState.POWERING_ON)

    #     elif cls.state == PayloadState.POWERING_ON:
    #         # Wait for the Payload to be ready
    #         cls.turn_on_power()

    #         if cls.time_we_started_booting == 0:
    #             cls.time_we_started_booting = cls._now

    #         if not cls.communication_interface.is_connected():
    #             if cls._interface_injected:
    #                 cls.initialize()
    #             else:
    #                 logger.error("Communication interface not injected yet.")
    #         else:
    #             logger.info("Communication interface is connected.")

    #             # The serial link will be purged by the payload when it opens its channel
    #             # so we ping to check until it is ready, i.e. the ping response is received
    #             if cls.ping():
    #                 cls._switch_to_state(PayloadState.READY)
    #                 logger.info(f"Payload is ready. Full boot in  {cls._now - cls.time_we_started_booting} seconds.")
    #                 cls.time_we_started_booting = 0  # Reset the boot time
    #             elif (
    #                 cls._now - cls.time_we_started_booting > cls.TIMEOUT_BOOT
    #             ):  # we seemingly failed --> attempt again to turn on
    #                 cls.turn_off_power()  # turn off the power line, just in case
    #                 cls._switch_to_state(PayloadState.OFF)  # Switch to OFF state
    #                 cls.last_error = ErrorCodes.TIMEOUT_BOOT  # Log error
    #                 cls.time_we_started_booting = 0  # Reset the boot time
    #                 # CDH / HAL notification
    #                 cls.must_re_attempt_boot = True  # Set the flag to re-attempt booting

    #     elif cls.state == PayloadState.READY:

    #         # logger.info(f"Is a command pending? {cls._did_we_send_a_command()}")
    #         # logger.info(f"Cmd sent: {cls.cmd_sent}")

    #         if not cls._did_we_send_a_command():  # Add timeout for retry
    #             # Check for telemetry (but not during active file transfer)
    #             if (
    #                 not FileTransfer.in_progress
    #                 and cls._now - cls._prev_tm_time > cls.telemetry_period
    #                 and not cls._not_waiting_tm_response
    #             ):
    #                 cls.request_telemetry()

    #         if not cls._did_we_send_a_command():  # Add timeout for retry
    #             if FileTransfer.in_progress:
    #                 # Check if we need to request the next file packet(s)
    #                 if not cls.just_requested_file_packet:
    #                     logger.info(f"[DEBUG] Requesting packets: USE_BATCH_TRANSFER={cls.USE_BATCH_TRANSFER}")
    #                     if cls.USE_BATCH_TRANSFER:
    #                         cls.request_next_file_packets()
    #                     else:
    #                         cls.request_next_file_packet()

    #         # Coming soon :)
    #         # Check OD states
    #         # For now, just ping the OD status

    #         cls.receive_response()

    #     elif cls.state == PayloadState.SHUTTING_DOWN:
    #         # Wait for the Payload to shutdown

    #         cls.receive_response()

    #         if cls.payload_sw_has_shutdown:
    #             logger.info("Payload SW has shutdown properly.")
    #             cls.turn_off_power()
    #             cls._switch_to_state(PayloadState.OFF)

    #         if cls.time_we_sent_shutdown + cls.TIMEOUT_SHUTDOWN < TPM.monotonic():
    #             # We have waited too long
    #             # Force the shutdown by cutting the power
    #             cls.turn_off_power()
    #             logger.warning("Timeout while shutting down. Force shutdown.")
    #             cls.last_error = ErrorCodes.TIMEOUT_SHUTDOWN

    # @classmethod
    # def receive_response(cls):
    #     """
    #     Poll for response with timeout.
    #     For batch requests, this will receive multiple packets.
    #     """
    #     # Check if we're expecting a batch response
    #     if cls.last_cmd_sent == CommandID.REQUEST_NEXT_FILE_PACKETS:
    #         return cls.receive_batch_response()

    #     # Regular single-packet response
    #     timeout = 0.015  # 15ms timeout
    #     poll_interval = 0.001  # Check every 1ms
    #     start_time = TPM.monotonic()

    #     recv = bytearray()
    #     while TPM.monotonic() - start_time < timeout:
    #         recv = cls.communication_interface.receive()
    #         if recv:
    #             # Check if this is the response we're expecting
    #             if cls.last_cmd_sent is not None:
    #                 # Peek at command ID (first byte of packet)
    #                 if len(recv) >= 1:
    #                     received_cmd_id = recv[0]
    #                     if received_cmd_id != cls.last_cmd_sent:
    #                         logger.warning(
    #                             f"[DEBUG] Skipping mismatched response: expected cmd_id={cls.last_cmd_sent:02x}, got {received_cmd_id:02x}"  # noqa: E501
    #                         )
    #                         recv = bytearray()  # Clear and continue polling
    #                         continue
    #             # Got the right response!
    #             break
    #         TPM.sleep(poll_interval)

    #     if recv:
    #         res = Decoder.decode(recv)
    #         cls.cmd_sent -= 1
    #         cls.last_cmd_sent = None  # Clear after receiving
    #     else:
    #         res = ErrorCodes.NO_RESPONSE
    #     return cls.handle_responses(res)

    # @classmethod
    # def receive_batch_response(cls):
    #     """
    #     Receive multiple packets for a batch request.
    #     The Jetson sends N packets back-to-back after a batch request.
    #     """

    #     Resp_RequestNextFilePackets.reset()

    #     # Calculate expected packet count
    #     start_packet = FileTransfer.packet_nb
    #     expected_count = min(cls.BATCH_SIZE, 317 - start_packet + 1)

    #     logger.info(f"[DEBUG] Expecting {expected_count} packets in batch")

    #     safety_multiplier = 1.3
    #     min_timeout = 0.1
    #     timeout = max(min_timeout, cls._EST_PKT_TX_TIME * expected_count * safety_multiplier)
    #     poll_interval = 0.001  # 1ms polling for lower latency
    #     start_time = TPM.monotonic()

    #     packets_received = 0
    #     end_of_file_reached = False
    #     arrival_times = []
    #     while packets_received < expected_count and TPM.monotonic() - start_time < timeout:
    #         recv = cls.communication_interface.receive()
    #         if recv:
    #             # Decode this packet
    #             res = Decoder.decode(recv)

    #             if res == ErrorCodes.OK:
    #                 packets_received += 1
    #                 arrival_times.append(TPM.monotonic())
    #             elif res == ErrorCodes.NO_MORE_FILE_PACKET:
    #                 # End of file reached - this is normal when batch request extends past file end
    #                 logger.info(f"[DEBUG] End of file reached after {packets_received} packets in batch")
    #                 end_of_file_reached = True
    #                 break  # Exit loop, process packets received so far
    #             elif res != ErrorCodes.NO_RESPONSE:
    #                 # Other error (CRC failure, etc.)
    #                 logger.warning(f"[DEBUG] Batch response got error: {res}")
    #                 cls.cmd_sent -= 1
    #                 cls.last_cmd_sent = None
    #                 return cls.handle_responses(res)

    #         # Always sleep between polls to allow UART buffer to fill
    #         TPM.sleep(poll_interval)

    #     cls.cmd_sent -= 1
    #     cls.last_cmd_sent = None

    #     if end_of_file_reached:
    #         # End of file reached - process packets received and mark transfer complete
    #         if packets_received > 0:
    #             logger.info(f"[DEBUG] Batch ended at EOF: {packets_received} packets received")
    #             # Process the packets we got, but signal EOF so transfer completes
    #             # We need to save packets first (via OK), then signal completion
    #             cls.handle_responses(ErrorCodes.OK)  # This saves the packets
    #             return cls.handle_responses(ErrorCodes.NO_MORE_FILE_PACKET)  # This completes transfer
    #         else:
    #             logger.info("[DEBUG] End of file reached, no more packets")
    #             return cls.handle_responses(ErrorCodes.NO_MORE_FILE_PACKET)
    #     elif packets_received == 0:
    #         logger.error("[DEBUG] Batch: No packets received")
    #         return cls.handle_responses(ErrorCodes.NO_RESPONSE)
    #     elif packets_received < expected_count:
    #         logger.warning(f"[DEBUG] Batch incomplete: got {packets_received}/{expected_count} packets")
    #         # Treat as CRC failure to trigger retry
    #         # If we received some packets in this (partial) batch, save them now so
    #         # we don't lose progress. The next batch should start at the first
    #         # packet that was not received.
    #         # We received a partial batch. Leave the received packets in
    #         # Resp_RequestNextFilePackets for `handle_responses()` to process
    #         # (so all packet saving / acking logic is centralized there).
    #         return cls.handle_responses(ErrorCodes.INVALID_PACKET)
    #     else:
    #         logger.info(f"[DEBUG] Batch complete: {packets_received} packets")
    #         return cls.handle_responses(ErrorCodes.OK)

    # @classmethod
    # def handle_responses(cls, resp):
    #     """
    #     Handle the status of the responses received from the Payload.
    #     """
    #     if resp:  # there is a response
    #         sent_cmd_id = Decoder.current_command_id()

    #         if sent_cmd_id == CommandID.REQUEST_TELEMETRY and resp == ErrorCodes.OK:
    #             cls._prev_tm_time = cls._now
    #             cls._not_waiting_tm_response = False
    #             cls.log_telemetry()
    #             return True

    #         elif sent_cmd_id == CommandID.REQUEST_IMAGE and resp == ErrorCodes.OK:
    #             # Start the file transfer
    #             FileTransfer.start_transfer(FileTransferType.IMAGE)
    #             logger.info("File transfer started.")
    #             cls.just_requested_file_packet = False
    #             cls.packet_retry_count = 0  # Reset retry counter for new transfer
    #             cls.packets_skipped_after_max_retries = 0  # Reset skip counter
    #             cls.cmd_sent = 0  # Reset command counter to allow file packet requests
    #             return True

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.OK:
    #             # Continue the file transfer, packet received successfully
    #             cls.just_requested_file_packet = False
    #             cls.packet_retry_count = 0  # Reset retry counter on success
    #             cls.total_packets_received += 1
    #             cls.cmd_sent = 0  # Reset command counter to allow next packet request

    #             # Log the received packet data (only actual payload)
    #             DH.log_file("img", Resp_RequestNextFilePacket.received_data[: Resp_RequestNextFilePacket.received_data_size])
    #             FileTransfer.ack_packet()  # increment the counter to next packet
    #             return True

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.INVALID_PACKET:
    #             # CRC verification failed or packet corrupted - retry same packet
    #             cls.packet_retry_count += 1
    #             cls.crc_failure_count += 1
    #             cls.just_requested_file_packet = False  # Allow retry

    #             if cls.packet_retry_count >= cls.MAX_PACKET_RETRIES:
    #                 # Max retries exceeded, skip this packet and continue with rest of file
    #                 logger.error(
    #                     f"CRC failed {cls.MAX_PACKET_RETRIES} times for packet {FileTransfer.packet_nb}, inserting empty packet and continuing"  # noqa: E501
    #                 )

    #                 # Log empty 240-byte packet to mark the corrupted/missing data
    #                 empty_packet = bytearray(240)  # All zeros
    #                 DH.log_file("img", empty_packet)

    #                 cls.packets_skipped_after_max_retries += 1

    #                 # Move to next packet
    #                 FileTransfer.ack_packet()
    #                 cls.packet_retry_count = 0  # Reset retry counter for next packet
    #                 cls.last_error = ErrorCodes.INVALID_PACKET  # Still track that we had an error

    #                 return False  # Indicate error occurred, but continue transfer
    #             else:
    #                 # Retry the same packet (don't increment packet_nb)
    #                 cls.total_packets_retried += 1
    #                 logger.warning(
    #                     f"CRC failed for packet {FileTransfer.packet_nb}, retry {cls.packet_retry_count}/{cls.MAX_PACKET_RETRIES}"  # noqa: E501
    #                 )
    #                 # DON'T call FileTransfer.ack_packet() - we want to retry the SAME packet
    #                 return False

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.NO_RESPONSE:
    #             # No response or incomplete packet received - retry same packet
    #             cls.packet_retry_count += 1
    #             cls.just_requested_file_packet = False  # Allow retry

    #             if cls.packet_retry_count >= cls.MAX_PACKET_RETRIES:
    #                 # Max retries exceeded, skip this packet
    #                 logger.error(
    #                     f"No response {cls.MAX_PACKET_RETRIES} times for packet {FileTransfer.packet_nb}, inserting empty packet and continuing"  # noqa: E501
    #                 )

    #                 # Log empty 240-byte packet
    #                 empty_packet = bytearray(240)
    #                 DH.log_file("img", empty_packet)

    #                 cls.packets_skipped_after_max_retries += 1

    #                 # Move to next packet
    #                 FileTransfer.ack_packet()
    #                 cls.packet_retry_count = 0

    #                 return False
    #             else:
    #                 # Retry the same packet
    #                 cls.total_packets_retried += 1
    #                 logger.warning(
    #                     f"No response for packet {FileTransfer.packet_nb}, retry {cls.packet_retry_count}/{cls.MAX_PACKET_RETRIES}"  # noqa: E501
    #                 )
    #                 return False

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKETS and resp == ErrorCodes.OK:
    #             # Batch transfer: receive multiple packets at once
    #             cls.just_requested_file_packet = False
    #             cls.packet_retry_count = 0
    #             cls.cmd_sent = 0

    #             # Process all received packets
    #             for packet_data in Resp_RequestNextFilePackets.packets:
    #                 cls.total_packets_received += 1
    #                 # Log packet data to file (only actual bytes)
    #                 DH.log_file("img", packet_data)
    #                 FileTransfer.ack_packet()  # Increment packet counter
    #             return True

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKETS and resp == ErrorCodes.INVALID_PACKET:
    #             # CRC failure in batch - retry the same batch
    #             cls.packet_retry_count += 1
    #             cls.crc_failure_count += 1
    #             cls.just_requested_file_packet = False

    #             # CRITICAL: Reset the partially received batch to avoid double-counting
    #             Resp_RequestNextFilePackets.reset()

    #             if cls.packet_retry_count >= cls.MAX_PACKET_RETRIES:
    #                 # Skip this batch after max retries
    #                 batch_size = cls.BATCH_SIZE
    #                 logger.error(f"Batch failed {cls.MAX_PACKET_RETRIES} times, skipping {batch_size} packets")

    #                 # Log empty packets for the entire batch
    #                 for _ in range(batch_size):
    #                     empty_packet = bytearray(240)
    #                     DH.log_file("img", empty_packet)
    #                     FileTransfer.ack_packet()
    #                     cls.packets_skipped_after_max_retries += 1

    #                 cls.packet_retry_count = 0
    #                 return False
    #             else:
    #                 cls.total_packets_retried += 1
    #                 logger.warning(f"Batch CRC failed, retry {cls.packet_retry_count}/{cls.MAX_PACKET_RETRIES}")
    #                 return False

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKETS and resp == ErrorCodes.NO_RESPONSE:
    #             # No response for batch - retry

    #             cls.packet_retry_count += 1
    #             cls.just_requested_file_packet = False

    #             # CRITICAL: Reset the partially received batch to avoid double-counting
    #             Resp_RequestNextFilePackets.reset()

    #             if cls.packet_retry_count >= cls.MAX_PACKET_RETRIES:
    #                 batch_size = cls.BATCH_SIZE
    #                 logger.error(f"Batch no response {cls.MAX_PACKET_RETRIES} times, skipping {batch_size} packets")

    #                 for _ in range(batch_size):
    #                     empty_packet = bytearray(240)
    #                     DH.log_file("img", empty_packet)
    #                     FileTransfer.ack_packet()
    #                     cls.packets_skipped_after_max_retries += 1

    #                 cls.packet_retry_count = 0
    #                 return False
    #             else:
    #                 cls.total_packets_retried += 1
    #                 logger.warning(f"Batch no response, retry {cls.packet_retry_count}/{cls.MAX_PACKET_RETRIES}")
    #                 return False

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKETS and resp == ErrorCodes.NO_MORE_FILE_PACKET:
    #             # Batch transfer complete
    #             cls.no_more_file_packet_to_receive = True
    #             FileTransfer.stop_transfer()
    #             DH.file_completed("img")

    #             if cls.packets_skipped_after_max_retries > 0:
    #                 logger.warning(
    #                     f"Completed image transfer with CORRUPTION: {cls.total_packets_received} packets received, {cls.packets_skipped_after_max_retries} packets corrupted, {cls.crc_failure_count} CRC failures, {cls.total_packets_retried} retries"  # noqa: E501
    #                 )
    #             else:
    #                 logger.info(
    #                     f"Completed image transfer: {cls.total_packets_received} packets, {cls.crc_failure_count} CRC failures, {cls.total_packets_retried} retries"  # noqa: E501
    #                 )

    #             cls.crc_failure_count = 0
    #             cls.total_packets_received = 0
    #             cls.total_packets_retried = 0
    #             cls.packets_skipped_after_max_retries = 0
    #             cls.packet_retry_count = 0
    #             return True

    #         elif sent_cmd_id == CommandID.REQUEST_NEXT_FILE_PACKET and resp == ErrorCodes.NO_MORE_FILE_PACKET:
    #             cls.no_more_file_packet_to_receive = True
    #             FileTransfer.stop_transfer()
    #             DH.file_completed("img")

    #             # Log comprehensive transfer statistics
    #             if cls.packets_skipped_after_max_retries > 0:
    #                 logger.warning(
    #                     f"Completed image transfer with CORRUPTION: {cls.total_packets_received} packets received, {cls.packets_skipped_after_max_retries} packets corrupted (filled with zeros), {cls.crc_failure_count} total CRC failures, {cls.total_packets_retried} retries"  # noqa: E501
    #                 )
    #             else:
    #                 logger.info(
    #                     f"Completed image transfer: {cls.total_packets_received} packets, {cls.crc_failure_count} CRC failures, {cls.total_packets_retried} retries"  # noqa: E501
    #                 )

    #             # Reset statistics for next transfer
    #             cls.crc_failure_count = 0
    #             cls.total_packets_received = 0
    #             cls.total_packets_retried = 0
    #             cls.packets_skipped_after_max_retries = 0
    #             cls.packet_retry_count = 0
    #             return True

    #         elif sent_cmd_id == CommandID.SHUTDOWN and resp == ErrorCodes.OK:
    #             # Paylaod has confirmed that we have properly shutdown
    #             # Now we can safely turn off the power line, which we will do in the main run logic
    #             cls.payload_sw_has_shutdown = True

    #         else:
    #             logger.error(f"Command error received: {resp}")  # TODO: map to good string for logging purposes
    #             cls.last_error = resp
    #             return False
    #     return False

    # @classmethod
    # def ping(cls):
    #     cls.communication_interface.send(Encoder.encode_ping())
    #     cls.last_cmd_sent = CommandID.PING_ACK  # Track command
    #     resp = cls.communication_interface.receive()
    #     if resp:  # a ping is immediate so if we don't receive a response, we assume it is not connected
    #         return Decoder.decode(resp) == _PING_RESP_VALUE
    #     return False

    # @classmethod
    # def shutdown(cls):
    #     # Simply send the shutdown command
    #     cls.communication_interface.send(Encoder.encode_shutdown())
    #     cls.cmd_sent += 1
    #     cls.last_cmd_sent = CommandID.SHUTDOWN  # Track command
    #     cls.time_we_sent_shutdown = TPM.monotonic()

    # @classmethod
    # def request_telemetry(cls):
    #     logger.info("Requesting telemetry...")
    #     cls.communication_interface.send(Encoder.encode_request_telemetry())
    #     cls.cmd_sent += 1
    #     cls.last_cmd_sent = CommandID.REQUEST_TELEMETRY  # Track command
    #     cls._not_waiting_tm_response = True

    # @classmethod
    # def log_telemetry(cls):
    #     PayloadTM.print()
    #     if DH.data_process_exists("payload_tm"):
    #         cls.log_data[PAYLOAD_IDX.SYSTEM_TIME] = int(PayloadTM.SYSTEM_TIME)
    #         cls.log_data[PAYLOAD_IDX.SYSTEM_UPTIME] = int(PayloadTM.SYSTEM_UPTIME)
    #         cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_TIME] = int(PayloadTM.LAST_EXECUTED_CMD_TIME)
    #         cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_ID] = int(PayloadTM.LAST_EXECUTED_CMD_ID)
    #         cls.log_data[PAYLOAD_IDX.PAYLOAD_STATE] = int(PayloadTM.PAYLOAD_STATE)
    #         cls.log_data[PAYLOAD_IDX.ACTIVE_CAMERAS] = int(PayloadTM.ACTIVE_CAMERAS)
    #         cls.log_data[PAYLOAD_IDX.CAPTURE_MODE] = int(PayloadTM.CAPTURE_MODE)
    #         cls.log_data[PAYLOAD_IDX.CAM_STATUS_0] = int(PayloadTM.CAM_STATUS[0])
    #         cls.log_data[PAYLOAD_IDX.CAM_STATUS_1] = int(PayloadTM.CAM_STATUS[1])
    #         cls.log_data[PAYLOAD_IDX.CAM_STATUS_2] = int(PayloadTM.CAM_STATUS[2])
    #         cls.log_data[PAYLOAD_IDX.CAM_STATUS_3] = int(PayloadTM.CAM_STATUS[3])
    #         cls.log_data[PAYLOAD_IDX.IMU_STATUS] = int(PayloadTM.IMU_STATUS)
    #         cls.log_data[PAYLOAD_IDX.TASKS_IN_EXECUTION] = int(PayloadTM.TASKS_IN_EXECUTION)
    #         cls.log_data[PAYLOAD_IDX.DISK_USAGE] = int(PayloadTM.DISK_USAGE)
    #         cls.log_data[PAYLOAD_IDX.LATEST_ERROR] = int(cls.last_error)
    #         cls.log_data[PAYLOAD_IDX.TEGRASTATS_PROCESS_STATUS] = int(PayloadTM.TEGRASTATS_PROCESS_STATUS)
    #         cls.log_data[PAYLOAD_IDX.RAM_USAGE] = int(PayloadTM.RAM_USAGE)
    #         cls.log_data[PAYLOAD_IDX.SWAP_USAGE] = int(PayloadTM.SWAP_USAGE)
    #         cls.log_data[PAYLOAD_IDX.ACTIVE_CORES] = int(PayloadTM.ACTIVE_CORES)
    #         cls.log_data[PAYLOAD_IDX.CPU_LOAD_0] = int(PayloadTM.CPU_LOAD[0])
    #         cls.log_data[PAYLOAD_IDX.CPU_LOAD_1] = int(PayloadTM.CPU_LOAD[1])
    #         cls.log_data[PAYLOAD_IDX.CPU_LOAD_2] = int(PayloadTM.CPU_LOAD[2])
    #         cls.log_data[PAYLOAD_IDX.CPU_LOAD_3] = int(PayloadTM.CPU_LOAD[3])
    #         cls.log_data[PAYLOAD_IDX.CPU_LOAD_4] = int(PayloadTM.CPU_LOAD[4])
    #         cls.log_data[PAYLOAD_IDX.CPU_LOAD_5] = int(PayloadTM.CPU_LOAD[5])
    #         cls.log_data[PAYLOAD_IDX.GPU_FREQ] = int(PayloadTM.GPU_FREQ)
    #         cls.log_data[PAYLOAD_IDX.CPU_TEMP] = int(PayloadTM.CPU_TEMP)
    #         cls.log_data[PAYLOAD_IDX.GPU_TEMP] = int(PayloadTM.GPU_TEMP)
    #         cls.log_data[PAYLOAD_IDX.VDD_IN] = int(PayloadTM.VDD_IN)
    #         cls.log_data[PAYLOAD_IDX.VDD_CPU_GPU_CV] = int(PayloadTM.VDD_CPU_GPU_CV)
    #         cls.log_data[PAYLOAD_IDX.VDD_SOC] = int(PayloadTM.VDD_SOC)

    #         cls.log_data[PAYLOAD_IDX.TIME_PAYLOAD_CONTROLLER] = TPM.time()
    #         cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_STATE] = int(cls.state)
    #         cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_COMMUNICATION_INTERFACE_ID] = (
    #             cls._return_communication_interface_id() if cls._interface_injected else 0
    #         )
    #         cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_COMMUNICATION_INTERFACE_CONNECTED] = int(
    #             cls.communication_interface.is_connected()
    #         )
    #         cls.log_data[PAYLOAD_IDX.PAYLOAD_CONTROLLER_LAST_ERROR] = int(cls.last_error) if cls.last_error else 0

    #         DH.log_data("payload_tm", cls.log_data)

    # @classmethod
    # def _return_communication_interface_id(cls):
    #     if cls._interface_injected:
    #         return int(cls.communication_interface.get_id())
    #     else:
    #         logger.error("Communication interface not injected yet.")
    #         return None

    # @classmethod
    # def enable_cameras(cls):
    #     cls.communication_interface.send(Encoder.encode_enable_cameras())
    #     cls.cmd_sent += 1
    #     cls.last_cmd_sent = CommandID.ENABLE_CAMERAS  # Track command

    # @classmethod
    # def disable_cameras(cls):
    #     cls.communication_interface.send(Encoder.encode_disable_cameras())
    #     cls.cmd_sent += 1
    #     cls.last_cmd_sent = CommandID.DISABLE_CAMERAS  # Track command

    # @classmethod
    # def request_image_transfer(cls):
    #     # This starts the process for image transfer which will be executed in the background by the controller at each cycle
    #     if cls.state != PayloadState.READY:
    #         logger.error("Cannot request image transfer. Payload is not ready.")
    #         return False

    #     # Don't request new image if transfer already in progress
    #     if FileTransfer.in_progress:
    #         logger.warning("Image transfer already in progress, ignoring duplicate request")
    #         return False

    #     cmd_bytes = Encoder.encode_request_image()
    #     hex_str = " ".join(f"{b:02x}" for b in cmd_bytes[:10])
    #     logger.info(f"[DEBUG TX] Sending REQUEST_IMAGE command: {hex_str}")
    #     cls.communication_interface.send(cmd_bytes)
    #     cls.cmd_sent += 1
    #     cls.last_cmd_sent = CommandID.REQUEST_IMAGE  # Track command
    #     cls.no_more_file_packet_to_receive = False
    #     return True

    # @classmethod
    # def request_next_file_packet(cls):
    #     if cls.state != PayloadState.READY:
    #         logger.error("Cannot request next file packet. Payload is not ready.")
    #         return False

    #     if not cls.just_requested_file_packet:
    #         # Flush buffer before requesting file packet to clear any stale PING_ACKs
    #         cls.communication_interface.flush_rx_buffer()
    #         cls.communication_interface.send(Encoder.encode_request_next_file_packet(FileTransfer.packet_nb))
    #         cls.cmd_sent += 1
    #         cls.last_cmd_sent = CommandID.REQUEST_NEXT_FILE_PACKET  # Track command
    #         cls.just_requested_file_packet = True
    #         logger.info(f"Requesting next file packet {FileTransfer.packet_nb}...")
    #         return True

    # @classmethod
    # def request_next_file_packets(cls):
    #     """Request multiple file packets at once for faster transfer"""
    #     logger.info("[DEBUG] request_next_file_packets() called - BATCH MODE")

    #     if cls.state != PayloadState.READY:
    #         logger.error("Cannot request next file packets. Payload is not ready.")
    #         return False

    #     if not cls.just_requested_file_packet:
    #         # Calculate how many packets to request
    #         # Don't request beyond the end of file
    #         start_packet = FileTransfer.packet_nb
    #         count = min(cls.BATCH_SIZE, 317 - start_packet + 1)  # 317 total packets

    #         if count <= 0:
    #             # All packets received! Complete the transfer
    #             logger.info("All packets received, completing transfer")
    #             cls.no_more_file_packet_to_receive = True
    #             FileTransfer.stop_transfer()
    #             DH.file_completed("img")

    #             # Log comprehensive transfer statistics
    #             if cls.packets_skipped_after_max_retries > 0:
    #                 logger.warning(
    #                     f"Completed image transfer with CORRUPTION: {cls.total_packets_received} packets received, {cls.packets_skipped_after_max_retries} packets corrupted (filled with zeros), {cls.crc_failure_count} total CRC failures, {cls.total_packets_retried} retries"  # noqa: E501
    #                 )
    #             else:
    #                 logger.info(
    #                     f"Completed image transfer: {cls.total_packets_received} packets, {cls.crc_failure_count} CRC failures, {cls.total_packets_retried} retries"  # noqa: E501
    #                 )

    #             # Reset statistics for next transfer
    #             cls.crc_failure_count = 0
    #             cls.total_packets_received = 0
    #             cls.total_packets_retried = 0
    #             cls.packets_skipped_after_max_retries = 0
    #             cls.packet_retry_count = 0
    #             return False

    #         # Flush buffer before requesting
    #         cls.communication_interface.flush_rx_buffer()

    #         # Send batch request
    #         cls.communication_interface.send(Encoder.encode_request_next_file_packets(start_packet, count))
    #         cls.cmd_sent += 1
    #         cls.last_cmd_sent = CommandID.REQUEST_NEXT_FILE_PACKETS
    #         cls.just_requested_file_packet = True
    #         logger.info(f"Requesting batch: packets {start_packet} to {start_packet + count - 1}")
    #         return True

    # @classmethod
    # def file_transfer_in_progress(cls):
    #     return FileTransfer.in_progress

    # @classmethod
    # def turn_on_power(cls):
    #     # This should enable the power line
    #     # If the function is called again and the power line is already on, it SHOULD do nothing
    #     # This will be called multiple times in a row
    #     logger.debug("[PAYLOAD] Turning on power...")
    #     pass

    # @classmethod
    # def turn_off_power(cls):
    #     # This is an expensive and drastic operation on the HW so must be limited to strict necessity
    #     # Preferable after a shutdown command
    #     logger.debug("[PAYLOAD] Turning off power...")
    #     pass
