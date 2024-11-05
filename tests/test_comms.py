import pytest
from unittest.mock import MagicMock, patch
from flight.apps.comms.comms import COMMS_STATE, MSG_ID


# Mock SATELLITE for actual hardware interaction
@pytest.fixture
def satellite_radio():
    with patch("emulator.configuration.SATELLITE", autospec=True) as mock_satellite:
        mock_satellite.RADIO.listen = MagicMock()
        mock_satellite.RADIO.RX_available = MagicMock(return_value=True)
        mock_satellite.RADIO.read_fifo_buffer = MagicMock(return_value=bytes([0x01, 0x00, 0x02, 0x03, 0x04]))
        mock_satellite.RADIO.crc_error = MagicMock(return_value=0)
        mock_satellite.RADIO.rssi = MagicMock(return_value=100)
        mock_satellite.RADIO.send = MagicMock()

        from flight.apps.comms.comms import SATELLITE_RADIO

        return SATELLITE_RADIO


def test_get_state(satellite_radio):
    assert satellite_radio.get_state() == COMMS_STATE.TX_HEARTBEAT


def test_transition_state_rx_to_tx_heartbeat(satellite_radio):
    satellite_radio.state = COMMS_STATE.RX
    satellite_radio.gs_req_message_ID = MSG_ID.SAT_HEARTBEAT
    satellite_radio.transition_state(RX_COUNTER=0)
    assert satellite_radio.get_state() == COMMS_STATE.TX_HEARTBEAT


def test_file_get_metadata_no_filepath(satellite_radio):
    satellite_radio.set_filepath("")
    satellite_radio.file_get_metadata()
    assert satellite_radio.file_ID == 0x00
    assert satellite_radio.file_size == 0
    assert satellite_radio.file_message_count == 0


def test_file_get_metadata_with_filepath(satellite_radio):
    satellite_radio.set_filepath("dummy_path")
    with patch("os.stat", return_value=(0, 0, 0, 0, 0, 0, 1200, 0, 0, 0)):
        satellite_radio.file_get_metadata()
        assert satellite_radio.file_ID == 0x01
        assert satellite_radio.file_size == 1200
        assert satellite_radio.file_message_count == 5


def test_receive_message_crc_error(satellite_radio):
    # Mock read_fifo_buffer to return specific bytes when called
    satellite_radio.sat.RADIO.read_fifo_buffer = MagicMock(return_value=bytes([0x01, 0x00, 0x02, 0x03, 0x04]))
    # Mock crc_error to return 1 to simulate a CRC error
    satellite_radio.sat.RADIO.crc_error = MagicMock(return_value=1)

    gs_req_id = satellite_radio.receive_message()
    assert gs_req_id == 0x00
    assert satellite_radio.crc_count == 1


def test_transmit_file_metadata(satellite_radio):
    satellite_radio.file_get_metadata = MagicMock(return_value=None)
    satellite_radio.file_pack_metadata = MagicMock(return_value=bytes([0x01, 0x00, 0x00, 0x00, 0x04, 0x00, 0x01]))
    satellite_radio.transmit_file_metadata()
    assert satellite_radio.tx_message[:4] == bytes([MSG_ID.SAT_FILE_METADATA, 0x0, 0x0, 0x7])


def test_transmit_message_heartbeat(satellite_radio):
    satellite_radio.state = COMMS_STATE.TX_HEARTBEAT
    satellite_radio.tm_frame = bytearray([0x00, 0x01, 0x02])
    tx_id = satellite_radio.transmit_message()
    assert satellite_radio.tx_message == bytearray([0x00, 0x01, 0x02])
    assert tx_id == 0x00
