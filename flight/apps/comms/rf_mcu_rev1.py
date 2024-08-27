"""
Satellite radio class for Argus-1 CubeSat.
Message packing/unpacking for telemetry/image TX
and acknowledgement RX.
"""

import os
import time

from hal.configuration import SATELLITE


FILE_PKTSIZE = 252


class COMMS_STATE:
    TX_HEARTBEAT = 0x00

    RX = 0x01

    TX_METADATA = 0x02
    TX_FILEPKT  = 0x03


class MSG_ID:
    SAT_HEARTBEAT = 0x01

    GS_ACK  = 0x08
    SAT_ACK = 0x09

    SAT_FILE_METADATA = 0x10

    SAT_FILE_PKT = 0x20


class SATELLITE_RADIO:
    sat = SATELLITE
    state = COMMS_STATE.TX_HEARTBEAT

    tm_frame = bytearray(256)

    filepath = ""
    file_ID = 0x00
    file_size = 0
    file_message_count = 0 

    file_array = []

    tx_message = []

    rx_message_ID = 0x00
    rx_message_sequence_count = 0
    rx_message_size = 0
    rx_message_rssi = 0

    gs_rx_message_ID = 0x0
    gs_req_message_ID = 0x0
    gs_req_seq_count = 0

    crc_count = 0

    """
        Name: file_get_metadata
        Description: Get TX file metadata from flash 
    """

    @classmethod
    def file_get_metadata(self):
        if not(self.filepath):
            # No file at filepath
            self.file_ID = 0x00
            self.file_size = 0
            self.file_message_count = 0 

        else:
            # Valid filepath from DH, set size and message count 
            file_stat = os.stat(self.filepath)
            self.file_size = int(file_stat[6])
            self.file_message_count = int(self.file_size / FILE_PKTSIZE)

            if (self.file_size % FILE_PKTSIZE) > 0:
                self.file_message_count += 1

            self.file_packetize()
    
    """
        Name: file_packetize
        Description: Packetize TX file and store in file array for TX
    """

    @classmethod
    def file_packetize(self):
        # Initialize / empty file array
        self.file_array = []

        # Get file data
        bytes_remaining = self.file_size
        send_bytes = open(self.filepath, "rb")

        # Loop through file and store contents in an array
        while bytes_remaining > 0:
            if bytes_remaining >= FILE_PKTSIZE:
                self.file_array.append(send_bytes.read(FILE_PKTSIZE))
            else:
                self.file_array.append(send_bytes.read(bytes_remaining))

            bytes_remaining -= FILE_PKTSIZE

        # Close file when complete
        send_bytes.close()

    """
        Name: file_pack_metadata
        Description: Return file metadata for transmission
    """

    @classmethod
    def file_pack_metadata(self):
        return (
            self.file_ID.to_bytes(1, "big")
            + self.file_size.to_bytes(4, "big")
            + self.file_message_count.to_bytes(2, "big")
        )
    
    """
        Name: receive_message
        Description: Receive and unpack message from GS

        Timeout for RX is set to 1s (change for increasing / decreasing blocking time)
    """

    @classmethod
    def receive_message(self):
        # Get packet from radio over SPI
        packet = self.sat.RADIO.receive(timeout = 1)

        if packet is None:
            # Timeout in receiving packet
            self.state = COMMS_STATE.TX_HEARTBEAT
            self.gs_req_message_ID = 0x00

            return self.state

        # Check CRC error on received packet 
        crc_check = self.sat.RADIO.crc_error()

        # Increment internal CRC count 
        if crc_check > 0:
            self.crc_count += 1

        # Get RX message RSSI
        self.rx_message_rssi = self.sat.RADIO.rssi(raw=True)
        
        # Unpack RX message header 
        self.rx_message_ID = int.from_bytes(packet[0:1], "big")
        self.rx_message_sequence_count = int.from_bytes(packet[1:3], "big")
        self.rx_message_size = int.from_bytes(packet[3:4], "big")

        if self.rx_message_ID == MSG_ID.GS_ACK:
            # GS acknowledged and sent command
            self.gs_rx_message_ID = int.from_bytes(packet[4:5], "big")
            self.gs_req_message_ID = int.from_bytes(packet[5:6], "big")
            self.gs_req_seq_count = int.from_bytes(packet[6:8], "big")

            #TODO - Verify GS RX message ID with previously transmitted message ID
            #TODO - Verify CRC count was 0 for last received message

            if self.gs_req_message_ID == MSG_ID.SAT_FILE_METADATA:
                # Start new file TX sequence, get new filepath
                self.state = COMMS_STATE.TX_METADATA

            if self.gs_req_message_ID == MSG_ID.SAT_FILE_PKT:
                # Send file packet with specified sequence count 
                self.state = COMMS_STATE.TX_FILEPKT

            else:
                # Unknown message ID, return to default state
                self.state = COMMS_STATE.TX_HEARTBEAT
        
        else:
            # Unknown message ID, return to default state
            self.state = COMMS_STATE.TX_HEARTBEAT

        return self.state

    """
        Name: transmit_file_metadata
        Description: Generate TX message for file metadata
    """

    @classmethod
    def transmit_file_metadata(self):
        # Transmit stored image info
        tx_header = bytes(
            [
                (MSG_ID.SAT_FILE_METADATA),
                0x0,
                0x1,
                0x7,
            ]
        )
        tx_payload = self.file_pack_metadata()
        self.tx_message = tx_header + tx_payload

    """
        Name: transmit_file_pkt
        Description: Generate TX message for file packet
    """

    @classmethod
    def transmit_file_pkt(self):
        tx_header = (
            (MSG_ID.SAT_FILE_PKT).to_bytes(1, "big")
            + (self.gs_req_seq_count).to_bytes(2, "big")
            + len(self.file_array[self.gs_req_seq_count]).to_bytes(1, "big")
        )

        # Payload
        tx_payload = self.image_array[self.gs_req_seq_count]
        # Pack entire message
        self.tx_message = tx_header + tx_payload

    """
        Name: transmit_message
        Description: Transmit message via the LoRa module
    """

    @classmethod
    def transmit_message(self):
        # Check comms state and TX message accordingly 
        if (self.state == COMMS_STATE.TX_HEARTBEAT):
            # Transmit SAT heartbeat
            self.tx_message = self.tm_frame

        elif (self.state == COMMS_STATE.TX_METADATA):
            # Transmit file metatdata
            self.transmit_file_metadata()

        elif (self.state == COMMS_STATE.TX_METADATA):
            # Transmit file packets with requested sequence count 
            self.transmit_file_pkt()

        else:
            # Transmit SAT heartbeat
            self.state = COMMS_STATE.TX_HEARTBEAT
            self.tx_message = self.tm_frame

        # Send a message to GS
        self.sat.RADIO.send(self.tx_message)
        self.crc_count = 0
        self.state = COMMS_STATE.RX

        # Return TX message header 
        return int.from_bytes(self.tx_message[0:1], "big")