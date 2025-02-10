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
