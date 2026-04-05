"""
Payload Control Interface

This module defines the Payload Controller class, which is responsible for managing the main interface between
the host and the Payload.

Author: Ibrahima Sory Sow, Perrin Tong

"""

from apps.payload.uart_comms import PayloadUART as PU
from core import DataHandler as DH
from core import logger
from core.dh_constants import PAYLOAD_IDX
from core.time_processor import TimeProcessor as TPM
from apps.telemetry.splat.splat.telemetry_definition import COMMAND_IDS
from apps.comms.fifo import QUEUE_STATUS, TransmitQueue
from hal.configuration import SATELLITE

from apps.telemetry.splat.splat.telemetry_codec import Command, pack, unpack, Ack, Fragment, Report
from apps.telemetry.splat.splat.transport_layer import Transaction
from apps.payload.download_manager import DownloadManager

from micropython import const
from hal.argus_v4 import ArgusV4Components


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
    SUCCESS = 8
    FAIL = 9


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
    if state == "SUCCESS":    # this state will only be reached if the experiment is completed succesfully
        return PayloadState.SUCCESS  # used to send a message to the groundstation letting it know that the experiment has finished
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
    
    ACT_TS = 0         # time at which switched to active state
    ACT_TIMEOUT = 20   # max amount of seconds to wait to recieve jetson ack for experiment command
    
    PROC_TS = 0        # time at which switched to processing state
    PROC_TIMEOUT = 60  # max amounts of seconds to run the experiment
    
    DWN_TS = 0         # time at which switched to download state
    DWN_TIMEOUT = 50   # max amount of time to wait for fragments
    DWN_LAST_FRAGMENT_TS = 0  # time at which last fragment was received during download
    
    OFF_TS = 0         # time at which switched to turning off state
    OFF_TIMEOUT = 20   # time to wait for the jetson to respond to shutdown command befoer forcing shutdown

    TELEM_TS = 0       # time at which last telemetry was requested
    TELEM_PERIOD = 20  # request telemetry every 20s

    # Lets init uart connection.
    # TODO should this only be made once the jetson has been turned on?
    PU.connect()
    
    # # flags used to process commands and ack
    received_experiment_ack = False
    received_ping_ack = False
    received_off_ack = False
    received_experiment_finished = False
    received_all_files_sent = False
    
    waiting_shutdown = False  # this flag is set to true and it receives the turn off ack

    # Telemetry variables
    payload_tm_data_format = "QQQQ" + 14 * "B" + "H" + 2 * "B" + 3 * "H"
    log_data = [0] * len(payload_tm_data_format)

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
        previous_state = cls.current_state
        cls.current_state = map_state(state)
        
        # need to update the log data
        cls.log_data[PAYLOAD_IDX.PD_STATE_MAINBOARD] = cls.current_state
        DH.log_data("payload_tm", cls.log_data)
        
        
        # booting state needs to turn on the satellite
        if cls.current_state == PayloadState.BOOTING:
            logger.info("[PAYLOAD] -  Turning on jetson")
            cls.log_data[PAYLOAD_IDX.LATEST_ERROR] = 200 # starting a new experiment resetting the error
            cls.current_command = cls.get_first_command()    # choosing the command here to make sure that if boot fails we do not run the command again
            cls.remove_first_command()  
            cls.turn_on_power()
            
        # active state, need to get the desired command
        if cls.current_state == PayloadState.ACTIVE:  
            logger.info(f"[PAYLOAD] -  Selected command: {cls.current_command}")

        if cls.current_state == PayloadState.DOWNLOAD:
            cls.received_all_files_sent = False
            cls.DWN_LAST_FRAGMENT_TS = TPM.time()
        
        # turn off state needs to send turn off command
        if cls.current_state == PayloadState.OFF:
            logger.info("[PAYLOAD] -  Sending turn off command")
            cls.send_turn_off_command()

        # success state needs to send message to the ground
        if cls.current_state == PayloadState.SUCCESS:
            logger.info("[PAYLOAD] -  Switching to SUCCESS state")
            # lets generate a message to be send to the grounstation to let them know that the experiment has finished
            # TODO - would be nice to let the gs know how many files the experiment generated
            success_ack_message = Ack(0, COMMAND_IDS["EXPERIMENT"], f"Experiment succeeded")
            q_stat = TransmitQueue.push_packet(success_ack_message)
            if q_stat != QUEUE_STATUS.OK:
                logger.error("Failed to push finished ack experiment success message to transmit queue")

        # fail state needs to send message to the ground
        if cls.current_state == PayloadState.FAIL:
            logger.info("[PAYLOAD] -  Switching to FAIL state")
            
            # lets generate a message to be send to the grounstation to let them know that the experiment has failed
            # and the stage at which it failed
            failed_ack_message = Ack(4, COMMAND_IDS["EXPERIMENT"], f"Experiment failed at {previous_state}")
            q_stat = TransmitQueue.push_packet(failed_ack_message)
            if q_stat != QUEUE_STATUS.OK:
                logger.error("Failed to push failed ack experiment failure message to transmit queue")
            
            cls.log_data[PAYLOAD_IDX.LATEST_ERROR] = previous_state
            
    @classmethod
    def add_command(
        cls,
        ts,
        camera_bit_flag,
        level_of_processing,
        width,
        height,
        downscale_factor=2.0,
        camera_defaults_selector=-1,
        fps=0,
        wbmode=0,
        aelock=0,
        awblock=0,
        exposuretimerange_low=0,
        exposuretimerange_high=0,
        gainrange_low=0.0,
        gainrange_high=0.0,
        ispdigitalgainrange_low=0.0,
        ispdigitalgainrange_high=0.0,
        ee_mode=0,
        ee_strength=0.0,
        aeantibanding=0,
        exposurecompensation=0.0,
        tnr_mode=0,
        tnr_strength=0.0,
        saturation=0.0,
    ):
        """
        Given the information it will create the command and add it to the list
        it should add ordered by timestamp
        the command_list will be a list of lists. The inside list will contain the necessary info
            ts, camera_bit_flag, level_of_processing, width, height,
            downscale_factor,
            camera_defaults_selector, fps, wbmode, aelock, awblock,
            exposuretimerange_low, exposuretimerange_high,
            gainrange_low, gainrange_high,
            ispdigitalgainrange_low, ispdigitalgainrange_high,
            ee_mode, ee_strength, aeantibanding,
            exposurecompensation, tnr_mode, tnr_strength, saturation
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
        cls.command_list.append(
            (
                ts,
                camera_bit_flag,
                level_of_processing,
                width,
                height,
                downscale_factor,
                camera_defaults_selector,
                fps,
                wbmode,
                aelock,
                awblock,
                exposuretimerange_low,
                exposuretimerange_high,
                gainrange_low,
                gainrange_high,
                ispdigitalgainrange_low,
                ispdigitalgainrange_high,
                ee_mode,
                ee_strength,
                aeantibanding,
                exposurecompensation,
                tnr_mode,
                tnr_strength,
                saturation,
            )
        )
        cls.command_list.sort(key=lambda x: x[0])  # Sort by timestamp
        
        cls.log_data[PAYLOAD_IDX.NEXT_CMD_TIME] = ts if ts > 0 else TPM.time()
        logger.warning(f"[PAYLOAD] - Next command time: {cls.log_data[PAYLOAD_IDX.NEXT_CMD_TIME]}")
        
        logger.info(f"[PAYLOAD] - Command added: {cls.command_list[-1]}")
        
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
        
        # create the command
        cmd_off = Command("TURN_OFF_PAYLOAD")
        
        # send the command
        PU.send(pack(cmd_off))
        
        logger.error("Please implement me")
        
    @classmethod 
    def process_uart(cls, max_packet_size=255):
        """
        This function will read from uart and try and process the commands/ack received
        """
        
        data = cls.read(max_packet_size)   # read the max packet size
        
        if not data:
            # nothing to be done here
            return False

        logger.info(f"[PAYLOAD] - Received data from uart: {data[0:10]} size: {len(data)}")
        
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
        # cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_TIME] = report.variables["PAYLOAD_TM"]["LAST_EXECUTED_CMD_TIME"] # this is not filled by jetsonz
        # cls.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_ID] = report.variables["PAYLOAD_TM"]["LAST_EXECUTED_CMD_ID"]     # this is not filled by jetsonz
        # cls.log_data[PAYLOAD_IDX.PD_STATE_MAINBOARD] = report.variables["PAYLOAD_TM"]["PD_STATE_MAINBOARD"]         # this is not filled by the jetson report data
        cls.log_data[PAYLOAD_IDX.PD_STATE_JETSON] = report.variables["PAYLOAD_TM"]["PD_STATE_JETSON"]
        # cls.log_data[PAYLOAD_IDX.LATEST_ERROR] = report.variables["PAYLOAD_TM"]["LATEST_ERROR"]
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
        
        
    @classmethod
    def process_ack(cls, ack):
        """
        It will check the ack command id and set the corresponding variable to true
        """
        logger.info(f"[PAYLOAD] - Processing ack: {ack}")
        # see if it was a ping ack
        if ack.cmd_id == COMMAND_IDS["PING"]:
            # it was a ping command
            if cls.received_ping_ack == True:
                logger.error("[PAYLOAD] - PING ACK OVERRIDDEN")
            cls.received_ping_ack = True
            logger.info("[PAYLOAD] - received_ping_ack set to true")
            return
            
        # see if it was a experiment ack
        if ack.cmd_id == COMMAND_IDS["EXPERIMENT"]:
            # it was a experiment command
            if cls.received_experiment_ack == True:
                logger.error("[PAYLOAD] - EXPERIMENT ACK OVERRIDDEN")
            cls.received_experiment_ack = True
            return
    
        # see if it was a off ack
        if ack.cmd_id == COMMAND_IDS["TURN_OFF_PAYLOAD"]:
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
        cls.transaction_dict[tid] = Transaction(tid, filename, number_of_packets=-1, max_payload_size=600)

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
        cls.DWN_LAST_FRAGMENT_TS = TPM.time()
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
        logger.debug("[PAYLOAD] Turning on Jetson power...")
        # try:
        #     ArgusV4Components.JETSON_ENABLE.value = True #TODO:Write a jetson available function in cubesat.py? 
        #     logger.info("[PAYLOAD] Jetson power enabled successfully.")
        #     return True
        # except Exception as e:
        #     logger.error(f"[PAYLOAD] Failed to enable payload power: {e}")
        #     return False
    
    @classmethod
    def turn_off_power(cls):
        """
        This should turn off power to the jetson
        """
        logger.error("[PAYLOAD] - Turning off power to jetson, please implement this method")
        # try:
        #     #Perform graceful shutdown
        #     if (cls.shutdown_jetson_process()):
        #         logger.info("[PAYLOAD] Shutdown command sent successfully, waiting for payload to shutdown before cutting power")
        #         ArgusV4Components.JETSON_ENABLE.value = False
        #         return True
        #     logger.error("[PAYLOAD] Graceful shutdown not successful")
        #     return False
        # except Exception as e:
        #     logger.error(f"[PAYLOAD] Failed to disable payload power: {e}")
        #     return False

    @classmethod
    def shutdown_jetson_process_gracefully(cls):
        """
        This should gracefully shutdown the jetson and 
        """
        logger.error("[PAYLOAD] - Shutting down jetson gracefully, please implement this method")
        return False


