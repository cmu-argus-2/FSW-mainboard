import pytest

from flight.apps.eps.eps import EPS_POWER_FLAG, EPS_POWER_THRESHOLD, EPS_SOC_THRESHOLD, GET_EPS_POWER_FLAG, GET_POWER_STATUS


# Invalid SOC values
@pytest.mark.parametrize("soc", [-2, 101])
@pytest.mark.parametrize(
    "state", [EPS_POWER_FLAG.NONE, EPS_POWER_FLAG.LOW_POWER, EPS_POWER_FLAG.NOMINAL, EPS_POWER_FLAG.EXPERIMENT]
)
def test_invalid_soc_values(state, soc):
    assert GET_EPS_POWER_FLAG(state, soc) == EPS_POWER_FLAG.NONE


# Invalid current state values
@pytest.mark.parametrize("state", [-1, 4, 10])
def test_invalid_current_state_values(state):
    soc = 50
    assert GET_EPS_POWER_FLAG(state, soc) == EPS_POWER_FLAG.NONE


# Low power SOC range
@pytest.mark.parametrize("soc", [EPS_SOC_THRESHOLD.LOW_POWER_ENTRY, EPS_SOC_THRESHOLD.LOW_POWER_ENTRY / 2, 0])
@pytest.mark.parametrize(
    "state", [EPS_POWER_FLAG.NONE, EPS_POWER_FLAG.LOW_POWER, EPS_POWER_FLAG.NOMINAL, EPS_POWER_FLAG.EXPERIMENT]
)
def test_low_power_soc_range(state, soc):
    assert GET_EPS_POWER_FLAG(state, soc) == EPS_POWER_FLAG.LOW_POWER


# Low power entry - low power exit range
@pytest.mark.parametrize("soc", [EPS_SOC_THRESHOLD.LOW_POWER_ENTRY + 1, EPS_SOC_THRESHOLD.LOW_POWER_EXIT - 1])
def test_low_power_entry_exit_range(soc):
    # Only casing on low power and nominal states since experiment state EPS logic is not yet finalized
    assert GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc) != EPS_POWER_FLAG.LOW_POWER
    assert GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc) == EPS_POWER_FLAG.LOW_POWER
    assert GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc) != EPS_POWER_FLAG.LOW_POWER


# Low power exit range and above
@pytest.mark.parametrize(
    "soc",
    [
        EPS_SOC_THRESHOLD.LOW_POWER_EXIT,
        EPS_SOC_THRESHOLD.LOW_POWER_EXIT + 1,
        (EPS_SOC_THRESHOLD.LOW_POWER_EXIT + 100) / 2,
        100,
    ],
)
@pytest.mark.parametrize("state", [EPS_POWER_FLAG.NONE, EPS_POWER_FLAG.LOW_POWER, EPS_POWER_FLAG.NOMINAL])
def test_low_power_exit_range(state, soc):
    assert GET_EPS_POWER_FLAG(state, soc) != EPS_POWER_FLAG.LOW_POWER


@pytest.mark.parametrize(
    "power_values, threshold, expected_status",
    [
        ([200, 400, 600, 800, 1000], EPS_POWER_THRESHOLD.RADIO, False),  # Below threshold
        ([700, 800, 900, 800, 1000], EPS_POWER_THRESHOLD.MAINBOARD, True),  # Above threshold
        ([10000, 15000, 16000, 17000, 18000], EPS_POWER_THRESHOLD.JETSON, False),  # Below
        ([15000, 18000, 17000, 17000, 18000], EPS_POWER_THRESHOLD.JETSON, True),  # Above
        ([100, 200, 300, 400, 500], EPS_POWER_THRESHOLD.MAINBOARD, False),  # Below
        ([1000, 1200, 1700, 1600, 2000], EPS_POWER_THRESHOLD.TORQUE_COIL, True),  # Just at threshold
        ([600, 700, 750, 800, 850], EPS_POWER_THRESHOLD.RADIO, True),  # Just above
        ([100, 1000], EPS_POWER_THRESHOLD.MAINBOARD, False),  # Below
    ],
)
def test_get_power_status(power_values, threshold, expected_status):
    buf = []
    for power in power_values[:-1]:  # Fill buffer except last value
        GET_POWER_STATUS(buf, power, threshold, 5)

    final_status, avg_power = GET_POWER_STATUS(buf, power_values[-1], threshold, 5)
    assert final_status == expected_status
