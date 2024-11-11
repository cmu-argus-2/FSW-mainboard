from unittest.mock import MagicMock, patch  # noqa F401

import pytest

from flight.apps.comms.comms import COMMS_STATE, MSG_ID  # noqa F401


# Mock SATELLITE for actual hardware interaction
@pytest.fixture
def satellite_radio():
    with patch("emulator.configuration.SATELLITE", autospec=True) as mock_satellite:
        mock_satellite.RADIO.RX_available = MagicMock(return_value=True)
        mock_satellite.RADIO.send = MagicMock()

        from flight.apps.comms.comms import SATELLITE_RADIO

        return SATELLITE_RADIO


# Tests based on statechart transitions
def test_1_statechart_init(satellite_radio):
    assert satellite_radio.get_state() == COMMS_STATE.TX_HEARTBEAT


def test_1_statechart_timeout(satellite_radio):
    satellite_radio.state = COMMS_STATE.RX

    satellite_radio.transition_state(True)
    assert satellite_radio.get_state() == COMMS_STATE.TX_HEARTBEAT


def test_1_statechart_T1(satellite_radio):
    satellite_radio.state = COMMS_STATE.RX

    satellite_radio.gs_req_message_ID = MSG_ID.SAT_HEARTBEAT
    satellite_radio.transition_state(False)
    assert satellite_radio.get_state() == COMMS_STATE.TX_HEARTBEAT


def test_1_statechart_T2(satellite_radio):
    satellite_radio.state = COMMS_STATE.TX_HEARTBEAT

    satellite_radio.transition_state(False)
    assert satellite_radio.get_state() == COMMS_STATE.RX


def test_1_statechart_T3(satellite_radio):
    satellite_radio.state = COMMS_STATE.RX

    satellite_radio.gs_req_message_ID = MSG_ID.SAT_FILE_METADATA
    satellite_radio.transition_state(False)
    assert satellite_radio.get_state() == COMMS_STATE.TX_METADATA


def test_1_statechart_T4(satellite_radio):
    satellite_radio.state = COMMS_STATE.TX_METADATA

    satellite_radio.transition_state(False)
    assert satellite_radio.get_state() == COMMS_STATE.RX


def test_1_statechart_T7(satellite_radio):
    satellite_radio.state = COMMS_STATE.RX

    satellite_radio.gs_req_message_ID = MSG_ID.SAT_FILE_PKT
    satellite_radio.transition_state(False)
    assert satellite_radio.get_state() == COMMS_STATE.TX_FILEPKT


def test_1_statechart_T8(satellite_radio):
    satellite_radio.state = COMMS_STATE.TX_FILEPKT

    satellite_radio.transition_state(False)
    assert satellite_radio.get_state() == COMMS_STATE.RX