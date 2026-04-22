"""

Command Definitions

======================

This modules contains the definition of the command functions for the satellite.


Each command is defined as follows:
- ID: A unique identifier for the command.
- Name: A string representation of the command for debugging.
- Description: A brief description of the command.
- Arguments: A list of parameters that the command accepts.
- Precondition: A list of conditions that must be met before executing the command.

See the documentation for a full description of each command.

Author: Ibrahima S. Sow

"""

import supervisor
from apps.command.supervisor import CommandSupervisor
from apps.comms.comms import SATELLITE_RADIO
from apps.comms.fifo import QUEUE_STATUS, TransmitQueue
from apps.comms.modes import COMMS_MODE as COMMS_MODE_ID
from apps.comms.modes import COMMS_MODE_STR
from apps.digipeater import DigipeaterState
from apps.telemetry.middleware import Frame as TelemetryFrame
from apps.telemetry.splat.splat.telemetry_codec import Command
from apps.telemetry.splat.splat.transport_layer import transaction_manager as TM
from core import logger
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STR_STATES
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE

FILE_PKTSIZE = 240
COMMAND_REGISTRY = {}


def register_command(name=None):
    """Decorator to register a command handler in COMMAND_REGISTRY."""

    def decorator(func):
        command_name = name or func.__name__
        COMMAND_REGISTRY[command_name] = func
        return func

    return decorator

@register_command()
def FORCE_REBOOT():
    """Forces a power cycle of the spacecraft."""
    logger.info("Executing FORCE_REBOOT")
    supervisor.reload()
    return []

@register_command()
def GRACEFUL_REBOOT():
    """
    Attempt to gracefully reboot the satellite
    this is equivalente to the reboot every 24h
    """

    logger.info("Executing GRACEFUL_REBOOT")
    try:
        
        # shutdown DH to make sure all files are closed properly
        response = DH.graceful_shutdown()
        
        if not response:
            logger.error("Failed to gracefully shutdown data handler, aborting reboot")
            return ["graceful reboot failed: DH shutdown failed"]
        
        SATELLITE.reboot()
        
        return ["success"] # this will never be returned
    except Exception as e:
        logger.error(f"Failed to gracefully reboot the satellite: {e}")
        return ["graceful reboot failed: {e}"]
    

@register_command()
def MAIN_POWER_REBOOT():
    logger.info("Executing MAIN_POWER_REBOOT")
    try:
        SATELLITE.reboot()
        return ["success"] # this will never be returned
    except Exception as e:
        logger.error(f"Failed to reboot the satellite: {e}")
        return ["main power reboot failed"]
    
@register_command()
def PET_REBOOT():
    """
    This will update the _BOOT_TIME in hal_monitor to make prevent the satellite from performing
    the regular reboot for the next 24 hours
    """
    logger.info("Executing PET_REBOOT")

    try:
        from tasks import hal_monitor

        current_time = TPM.monotonic()
        hal_monitor._BOOT_TIME = current_time
        return ["pet successfull"]
    except Exception as e:
        logger.error(f"[PET_REBOOT] Failed to reset regular reboot timer: {e}")
        return [f"pet failed: {e}"]


@register_command()
def PING(string="Hello From Space!"):
    """
    Command to test the communication with the satellite
    will respond with whatever string it received
    """
    logger.info(f"Executing PING with string: {string}")
    return [string]


@register_command()
def SUM(opA, opB):
    """
    Test command
    used to experiment adding new command and testing the arguments
    """
    logger.info(f"Executing SUM with opA: {opA} and opB: {opB}")
    return [opA + opB]


@register_command()
def SWITCH_TO_STATE(target_state_id, time_in_state=None):
    """Forces a switch of the spacecraft to a specific state."""
    logger.info(f"Executing SWITCH_TO_STATE with target_state: {STR_STATES[target_state_id]}, time_in_state: {time_in_state}")
    SM.start_forced_state(target_state_id, time_in_state)
    return []


@register_command()
def UPLINK_TIME_REFERENCE(time_reference):
    """Sends a time reference to the spacecraft to update the time processing module."""
    logger.info(f"Executing UPLINK_TIME_REFERENCE with current_time: {time_reference}")
    TPM.set_time(time_reference)
    return []


@register_command()
def TURN_OFF_PAYLOAD():
    """Cuts the power to the payload"""
    logger.info("Executing TURN_OFF_PAYLOAD")

    if not SATELLITE.PAYLOADPOWER_AVAILABLE:
        logger.warning("[PAYLOAD] Payload power pins is not available.")
        return ["payload power pins not available"]

    try:
        logger.info("[PAYLOAD] Shutdown command sent successfully, waiting for payload to shutdown before cutting power")
        SATELLITE.JETSON_ENABLE.value = False
        TPM.sleep(0.1)
        SATELLITE.JETSON_SD_REQ.value = False  # turn of 5v dcdc to save more power

    except Exception as e:
        logger.error(f"[PAYLOAD] Failed to disable payload power: {e}")

    return []


@register_command()
def TURN_ON_PAYLOAD():
    """Enables power to the payload"""
    logger.info("Executing TURN_ON_PAYLOAD")

    if not SATELLITE.PAYLOADPOWER_AVAILABLE:
        logger.warning("[PAYLOAD] Payload power pins is not available.")
        return ["payload power pins not available"]

    try:
        SATELLITE.JETSON_SD_REQ.value = True
        TPM.sleep(0.1)
        SATELLITE.JETSON_ENABLE.value = True  # turn of 5v dcdc to save more power

        logger.info("[PAYLOAD] Jetson power enabled successfully.")
    except Exception as e:
        logger.error(f"[PAYLOAD] Failed to enable payload power: {e}")
    return []


@register_command()
def RF_STOP():
    """Stops all satellite RF transmissions."""
    logger.warning("Executing RF_STOP (deferred): will disable TX after ACK")
    CommandSupervisor.request_rf_stop()
    return ["rf_stop_requested"]


@register_command()
def RF_RESUME():
    """Resumes normal satellite RF transmissions."""
    logger.warning("Executing RF_RESUME: enabling standard satellite TX")
    CommandSupervisor.cancel_pending_rf_stop()
    SATELLITE_RADIO.set_comms_mode(COMMS_MODE_ID.STANDARD)
    return ["rf_resume_executed"]


@register_command()
def DIGIPEATER_ACTIVATE():
    """Activates the digipeater relay subsystem."""
    logger.warning("Executing DIGIPEATER_ACTIVATE")
    return DigipeaterState.activate()


@register_command()
def DIGIPEATER_DEACTIVATE():
    """Deactivates the digipeater relay subsystem."""
    logger.warning("Executing DIGIPEATER_DEACTIVATE")
    return DigipeaterState.deactivate()


@register_command()
def COMMS_MODE(mode_id):
    """Set COMMS operating mode (STANDARD/RF_STOP).

    RF_STOP is routed through CommandSupervisor for deferred execution
    (ACK first, then drain queue, then activate).
    """
    if mode_id == COMMS_MODE_ID.RF_STOP:
        logger.warning("Executing COMMS_MODE(RF_STOP) via deferred path")
        CommandSupervisor.request_rf_stop()
    else:
        SATELLITE_RADIO.set_comms_mode(mode_id)
        logger.warning(f"Executing COMMS_MODE: {COMMS_MODE_STR.get(mode_id, 'UNKNOWN')}")
    return []


@register_command()
def REQUEST_TM_NOMINAL():
    """Requests a nominal snapshot of all subsystems."""
    logger.info("Executing REQUEST_TM_NOMINAL")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_heartbeat()
    q_stat = TransmitQueue.push_packet(packet)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push nominal telemetry to transmit queue with status: {q_stat}")
    logger.info(f"Telemetry nominal packed and pushed to transmit queue {q_stat}")

    return [q_stat]


@register_command()
def REQUEST_TM_HAL():
    """Requests hardware-focused telemetry, including information on HAL, EPS, and errors."""
    logger.info("Executing REQUEST_TM_HAL")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_hal()
    q_stat = TransmitQueue.push_packet(packet)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push HAL telemetry to transmit queue with status: {q_stat}")
    logger.info(f"Telemetry hal packed and pushed to transmit queue {q_stat}")

    return [q_stat]


@register_command()
def REQUEST_TM_STORAGE():
    """Requests full storage status of the mainboard, including details on onboard processes."""
    logger.info("Executing REQUEST_TM_STORAGE")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_storage()
    q_stat = TransmitQueue.push_packet(packet)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push storage telemetry to transmit queue with status: {q_stat}")
    logger.info(f"Telemetry storage packed and pushed to transmit queue {q_stat}")

    return [q_stat]


@register_command()
def REQUEST_TM_PAYLOAD():
    """Requests telemetry data from the payload, provided it is on."""
    logger.info("Executing REQUEST_TM_PAYLOAD")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_payload()
    q_stat = TransmitQueue.push_packet(packet)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push payload telemetry to transmit queue with status: {q_stat}")
    logger.info(f"Telemetry payload packed and pushed to transmit queue {q_stat}")

    return [q_stat]


@register_command()
def EVAL_STRING_COMMAND(string_command):
    """
    As of right now this is just for debugging purposes
    will receive a string, will eval it and return the results.
    [TODO] - This is a potential security risk. Should create some sort of firewall that can be controlled
    with another command to allow/disallow evalling commands
    """
    logger.info(f"Executing EVAL_STRING_COMMAND with request: {string_command}")

    try:
        result = eval(string_command)
        return [result]
    except Exception as e:
        logger.error(f"EVAL_STRING_COMMAND execution failed: {e}")
        return ["eval_string_command_failed"]


@register_command()
def CREATE_TRANS(tid, string_command):
    logger.info(f"GS requesting the following file {string_command} and tid: {tid}")

    # 1. check if the file exists and get the path to the file
    # 2. create a transaction in the transaction manager
    transaction = TM.create_transaction(file_path=string_command, tid=tid, is_tx=True)
    if transaction is None:
        logger.error(f"Unable to create transaction {tid}")
        return ["transaction_creation_failed"]

    # 3. generate init transaction packet
    cmd = Command("INIT_TRANS")
    tid = transaction.tid
    n_packets = transaction.number_of_packets

    cmd.set_arguments(tid, n_packets)
    q_stat = TransmitQueue.push_packet(cmd)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push INIT_TRANS command to transmit queue with status: {q_stat}")

    return [tid, n_packets]


@register_command()
def GENERATE_ALL_PACKETS(tid):
    # 1. search for the transaction id
    transaction = TM.get_transaction(tid)
    if transaction is None:
        logger.error(f"Transaction with tid {tid} not found")
        return ["transaction_not_found"]

    # 2. generate all the packets for that transaction
    packet_list = transaction.generate_all_packets()
    # 3. add them to the transmit queue
    for packet in packet_list:
        q_stat = TransmitQueue.push_packet(packet)
        if q_stat != QUEUE_STATUS.OK:
            logger.error(f"Failed to push packet to transmit queue with status: {q_stat}")

    return [len(packet_list)]


@register_command()
def GENERATE_X_PACKETS(tid, x):
    # 1. search for the transaction id
    transaction = TM.get_transaction(tid)
    if transaction is None:
        logger.error(f"Transaction with tid {tid} not found")
        return ["transaction_not_found"]

    # 2. generate the packets
    packet_list = transaction.generate_x_packets(x)
    # 3. add them to the transmit queue
    for packet in packet_list:
        q_stat = TransmitQueue.push_packet(packet)
        if q_stat != QUEUE_STATUS.OK:
            logger.error(f"Failed to push packet to transmit queue with status: {q_stat}")

    return [len(packet_list)]


@register_command()
def GENERATE_SINGLE_PACKET(tid, seq_number):
    # 1. search for the transaction id
    transaction = TM.get_transaction(tid)
    if transaction is None:
        logger.error(f"Transaction with tid {tid} not found")
        return ["transaction_not_found"]

    # generate the packet
    packet = transaction.generate_specific_packet(seq_number)
    # 3. add it to the transmit queue
    q_stat = TransmitQueue.push_packet(packet)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push packet to transmit queue with status: {q_stat}")

    # Return the number of packets queued, for consistency with GENERATE_* commands
    return [1]


@register_command()
def CONFIRM_LAST_BATCH(tid, bitmap_high, bitmap_low):
    # 1. search for the transaction id
    transaction = TM.get_transaction(tid)
    if transaction is None:
        logger.error(f"Transaction with tid {tid} not found")
        return ["transaction_not_found"]

    # 2. confirm last batch
    len_missing_fragments = transaction.confirm_last_batch((bitmap_high, bitmap_low))

    return [len_missing_fragments]


@register_command()
def UPDATE_MISSING_FRAGMENTS(tid, seq_offset, bitmap_high, bitmap_low):
    # 1. search for the transaction id
    transaction = TM.get_transaction(tid)
    if transaction is None:
        logger.error(f"Transaction with tid {tid} not found")
        return ["transaction_not_found"]

    # 2. update missing fragments
    len_missing_fragments = transaction.update_missing_fragments_bitmap(seq_offset, (bitmap_high, bitmap_low))

    return [len_missing_fragments]


@register_command()
def TRANS_PAYLOAD(tid, seq_number, payload):
    # [TODO] - implement this command if there is the necessity to uplink files to the satellite
    # no need to implement now, this will only be needed if sending transactions from the gs to sat
    # return a structured "not implemented" response to avoid breaking downstream handling
    return ["not_implemented"]


@register_command()
def INIT_TRANS(tid, number_of_packets):
    # [TODO] - implement this command if there is the necessity to uplink files to the satellite
    # no need to implement now, this will only be needed if sending transactions from the gs to sat
    # return a structured "not implemented" response to avoid breaking downstream handling
    return ["not_implemented"]


@register_command()
def LIST_DIR(skip_elements, string_command):
    """
    Try and list whatever is on the given directory
    the result will be sent as a string, skip_elements will skip the first x elements
    """

    import os

    try:
        file_list = os.listdir(string_command)
    except Exception as e:
        return [f"error: {e}"]

    return file_list[skip_elements:]

@register_command()
def GET_FILE_SIZE(string_command):
    """
    Try and get the size of a file
    the result will be sent as a string
    """

    import os

    try:
        file_size = os.stat(string_command)[6]  # get the size of the file in bytes
    except Exception as e:
        return [f"error: {e}"]

    return [file_size]

@register_command()
def DELETE_ALL_FILES():
    """
    Simple command that will delete all files
    it will call datahandler function that will deal with it
    """

    try:
        DH.delete_all_files()
        supervisor.reload() # reload after deleting all files to clear any references to deleted files in memory and reset the state of the satellite
    except Exception as e:
        return [f"error: {e}"]
    return ["all files deleted"]


@register_command()
def UPDATE_SD_USAGE():
    """
    Calls the DH function to compute the sd card usage and update it on the DH
    it will also return the current sd_usage
    """

    try:
        DH.update_SD_usage()
        usage = DH.SD_usage()
    except Exception as e:
        return [f"error: {e}"]
    return ["sd usage updated", usage]


@register_command()
def EXPERIMENT(
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
    Command that will be called by the ground station to start an experiment
    ts                    -> the time at which the command should be ran (0 is to run now)
    camera_bit_flag       -> the first 4 bits will indicate which cameras should be used to take the picture
    level_of_processing   -> what level of processing to run TODO - add here the options
    resolution            -> The resolution of the images. They are taken at full resolution and scaled down
    """
    from apps.payload.controller import PayloadController as PC

    logger.info(f"[PAYLOAD] - Experiment command received to run at {ts}")
    result = PC.add_command(
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
    if not result:
        logger.error(f"[PAYLOAD] - Failed to add experiment command for timestamp {ts}")
    return result

@register_command()
def CLEAR_EXPERIMENT_LIST():
    """
    Command that will be called by the ground station to clear the list of scheduled experiments in the payload
    returns the number of experiments that were cleared from the list
    """
    from apps.payload.controller import PayloadController as PC


    logger.info(f"[PAYLOAD] - Clear experiment list command received")
    cleared_count = PC.clear_experiment_list()
    return [cleared_count]

@register_command()
def GET_EXPERIMENT_LIST(skip_elements=0):
    """
    Command that will be called by the ground station to get the list of scheduled experiments in the payload
    returns a list of experiments ts
    """
    from apps.payload.controller import PayloadController as PC

    logger.info(f"[PAYLOAD] - List experiments command received")
    experiment_list = PC.list_experiments()
    return experiment_list[skip_elements:]