import pytest
import random

from flight.apps.eps.eps import (
    EPS_POWER_FLAG,
    EPS_SOC_THRESHOLD,
    GET_EPS_POWER_FLAG
)

def test_EPS_POWER_FLAG():
    # Test all possible combinations of flags and SOC ranges for this function

    # Low power SOC range
    soc = random.randint(0, EPS_SOC_THRESHOLD.LOW_POWER_ENTRY)

    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc)
    assert(flag == EPS_POWER_FLAG.LOW_POWER)
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc)
    assert(flag == EPS_POWER_FLAG.LOW_POWER)
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc)
    assert(flag == EPS_POWER_FLAG.LOW_POWER)
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.EXPERIMENT, soc)
    assert(flag == EPS_POWER_FLAG.LOW_POWER)

    # Low power entry - low power exit range
    soc = random.randint(EPS_SOC_THRESHOLD.LOW_POWER_ENTRY + 1, EPS_SOC_THRESHOLD.LOW_POWER_EXIT)

    # Only casing on low power and nominal states since experiment state EPS logic is not yet finalized
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc)
    assert(flag != EPS_POWER_FLAG.LOW_POWER)
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc)
    assert(flag == EPS_POWER_FLAG.LOW_POWER)
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc)
    assert(flag != EPS_POWER_FLAG.LOW_POWER)

    # Low power exit range and above
    soc = random.randint(EPS_SOC_THRESHOLD.LOW_POWER_EXIT, 100)

    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc)
    assert(flag != EPS_POWER_FLAG.LOW_POWER)
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc)
    assert(flag != EPS_POWER_FLAG.LOW_POWER)
    flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc)
    assert(flag != EPS_POWER_FLAG.LOW_POWER)