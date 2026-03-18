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
from apps.command.constants import file_tags_str
from apps.comms.fifo import QUEUE_STATUS, TransmitQueue
from apps.telemetry.middleware import Frame as TelemetryFrame  # this will substitute for the old telemetry packer
from apps.telemetry.splat.splat.telemetry_codec import Command
from apps.telemetry.splat.splat.transport_layer import transaction_manager as TM
from core import logger
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STR_STATES
from core.time_processor import TimeProcessor as TPM

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
    # https://learn.adafruit.com/circuitpython-essentials/circuitpython-resetting
    return []


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
    """Sends a shutdown command to the payload and turns off its power line."""
    logger.info("Executing TURN_OFF_PAYLOAD")
    return []


@register_command()
def SCHEDULE_OD_EXPERIMENT():
    """Schedules an orbit determination experiment at the next available opportunity."""
    logger.info("Executing SCHEDULE_OD_EXPERIMENT")
    return []


@register_command()
def REQUEST_TM_NOMINAL():
    """Requests a nominal snapshot of all subsystems."""
    logger.info("Executing REQUEST_TM_NOMINAL")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_heartbeat()  #
    q_stat = TransmitQueue.push_packet(packet)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push nominal telemetry to transmit queue with status: {q_stat}")
    logger.info(f"Telemetry nominal packed and pushed to transmit queue {q_stat}")

    # might be interesting to differentiate between periodic hearbeats
    # might want to add that this is a response

    return [q_stat]  # return the queue status number


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

    return [q_stat]  # return the queue status number


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

    return [q_stat]  # return the queue status number


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

    return [q_stat]  # return the queue status number


@register_command()
def REQUEST_FILE_METADATA(file_id, file_time=None):
    """Requests metadata for a specific file from the spacecraft."""
    logger.info(f"Executing REQUEST_FILE_METADATA with file_tag: {file_id} and file_time: {file_time}")
    file_path = None
    file_tag = file_tags_str[file_id]

    if file_time is None or file_time == 0:
        # None or 0 means get the latest file
        file_path = DH.request_TM_path(file_tag, True)
    else:
        # Specify file_tag, latest = False and file_time
        file_path = DH.request_TM_path(file_tag, False, file_time)

    return [file_path]


# NOTE: REQUEST_FILE_PKT handled internally in comms
@register_command()
def REQUEST_FILE_PKT(file_id, file_time):
    raise NotImplementedError("Handled internally by comms subsystem")


@register_command()
def REQUEST_IMAGE():
    raise NotImplementedError("Not implemented")


@register_command()
def DOWNLINK_ALL(file_id, file_time=None):
    """Downlinks all packets for a specific file from the spacecraft."""
    logger.info(f"Executing DOWNLINK_ALL with file_tag: {file_id} and file_time: {file_time}")
    file_path = None
    file_tag = file_tags_str[file_id]

    if file_time is None or file_time == 0:
        # None or 0 means get the latest file
        file_path = DH.request_TM_path(file_tag)
    else:
        # Specify file_tag, latest = False and file_time
        file_path = DH.request_TM_path(file_tag, False, file_time)

    return [file_path]


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
    hash_MSB, hash_msb, hash_LSB = transaction.get_hash_as_integers()

    cmd.set_arguments(tid, n_packets, hash_MSB, hash_msb, hash_LSB)
    q_stat = TransmitQueue.push_packet(cmd)
    if q_stat != QUEUE_STATUS.OK:
        logger.error(f"Failed to push INIT_TRANS command to transmit queue with status: {q_stat}")

    return [tid, n_packets, hash_MSB, hash_LSB]


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
def GET_SINGLE_PACKET(tid, seq_number):
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
def CONFIRM_LAST_BATCH(tid, MSB, LSB):
    # 1. search for the transaction id
    transaction = TM.get_transaction(tid)
    if transaction is None:
        logger.error(f"Transaction with tid {tid} not found")
        return ["transaction_not_found"]

    # 2. confirm last batch
    bitmap = (MSB << 16) | LSB
    len_missing_fragments = transaction.confirm_last_batch(bitmap)

    return [len_missing_fragments]


@register_command()
def UPDATE_MISSING_FRAGMENTS(tid, seq_offset, MSB, LSB):
    # 1. search for the transaction id
    transaction = TM.get_transaction(tid)
    if transaction is None:
        logger.error(f"Transaction with tid {tid} not found")
        return ["transaction_not_found"]

    # 2. update missing fragments
    bitmap = (MSB << 16) | LSB
    len_missing_fragments = transaction.update_missing_fragments_bitmap(seq_offset, bitmap)

    return [len_missing_fragments]


@register_command()
def TRANS_PAYLOAD(tid, seq_number, payload):
    # [TODO] - implement this command if there is the necessity to uplink files to the satellite
    # no need to implement now, this will only be needed if sending transactions from the gs to sat
    # return a structured "not implemented" response to avoid breaking downstream handling
    return ["not_implemented"]


@register_command()
def INIT_TRANS(tid, number_of_packets, hash_MSB, hash_LSB):
    # [TODO] - implement this command if there is the necessity to uplink files to the satellite
    # no need to implement now, this will only be needed if sending transactions from the gs to sat
    # return a structured "not implemented" response to avoid breaking downstream handling
    return ["not_implemented"]


def get_tx_message_header():
    """ " Helper function to obtain the tx message header to send back"""
    return int.from_bytes(TelemetryFrame.FRAME()[0:1], "big")
