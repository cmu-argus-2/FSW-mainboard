import pytest

from flight.apps.eps.eps import EPS_POWER_FLAG, EPS_SOC_THRESHOLD, GET_EPS_POWER_FLAG


# Invalid SOC values
@pytest.mark.parametrize("soc", [-2, 101])
@pytest.mark.parametrize("state", [
    EPS_POWER_FLAG.NONE,
    EPS_POWER_FLAG.LOW_POWER,
    EPS_POWER_FLAG.NOMINAL,
    EPS_POWER_FLAG.EXPERIMENT
])
def test_invalid_soc_values(state, soc):
    assert GET_EPS_POWER_FLAG(state, soc) == EPS_POWER_FLAG.NONE


# Invalid current state values
@pytest.mark.parametrize("state", [-1, 4, 10])
def test_invalid_current_state_values(state):
    soc = 50
    assert GET_EPS_POWER_FLAG(state, soc) == EPS_POWER_FLAG.NONE


# Low power SOC range
@pytest.mark.parametrize("soc", [
    EPS_SOC_THRESHOLD.LOW_POWER_ENTRY,
    EPS_SOC_THRESHOLD.LOW_POWER_ENTRY / 2,
    0
])
@pytest.mark.parametrize("state", [
    EPS_POWER_FLAG.NONE,
    EPS_POWER_FLAG.LOW_POWER,
    EPS_POWER_FLAG.NOMINAL,
    EPS_POWER_FLAG.EXPERIMENT
])
def test_low_power_soc_range(state, soc):
    assert GET_EPS_POWER_FLAG(state, soc) == EPS_POWER_FLAG.LOW_POWER


# Low power entry - low power exit range
@pytest.mark.parametrize("soc", [
    EPS_SOC_THRESHOLD.LOW_POWER_ENTRY + 1,
    EPS_SOC_THRESHOLD.LOW_POWER_EXIT - 1
])
def test_low_power_entry_exit_range(soc):
    # Only casing on low power and nominal states since experiment state EPS logic is not yet finalized
    assert GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc) != EPS_POWER_FLAG.LOW_POWER
    assert GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc) == EPS_POWER_FLAG.LOW_POWER
    assert GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc) != EPS_POWER_FLAG.LOW_POWER


# Low power exit range and above
@pytest.mark.parametrize("soc", [
    EPS_SOC_THRESHOLD.LOW_POWER_EXIT,
    EPS_SOC_THRESHOLD.LOW_POWER_EXIT + 1,
    (EPS_SOC_THRESHOLD.LOW_POWER_EXIT + 100) / 2,
    100
])
@pytest.mark.parametrize("state", [
    EPS_POWER_FLAG.NONE,
    EPS_POWER_FLAG.LOW_POWER,
    EPS_POWER_FLAG.NOMINAL
])
def test_low_power_exit_range(state, soc):
    assert GET_EPS_POWER_FLAG(state, soc) != EPS_POWER_FLAG.LOW_POWER
