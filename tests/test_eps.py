from flight.apps.eps.eps import EPS_POWER_FLAG, GET_EPS_POWER_FLAG


def test_EPS_POWER_FLAG():
    # Test all possible combinations of flags and SOC ranges for this function

    # Invalid SOC values
    socs = [-2, 101]
    for soc in socs:
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc)
        assert flag == EPS_POWER_FLAG.NONE
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc)
        assert flag == EPS_POWER_FLAG.NONE
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc)
        assert flag == EPS_POWER_FLAG.NONE
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.EXPERIMENT, soc)
        assert flag == EPS_POWER_FLAG.NONE

    # Invalid current state values
    soc = 50
    states = [-1, 4, 10]
    for state in states:
        flag = GET_EPS_POWER_FLAG(state, soc)
        assert flag == EPS_POWER_FLAG.NONE
        flag = GET_EPS_POWER_FLAG(state, soc)
        assert flag == EPS_POWER_FLAG.NONE
        flag = GET_EPS_POWER_FLAG(state, soc)
        assert flag == EPS_POWER_FLAG.NONE
        flag = GET_EPS_POWER_FLAG(state, soc)
        assert flag == EPS_POWER_FLAG.NONE

    # Low power SOC range
    socs = [30, 20, 0, 10]
    for soc in socs:
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc)
        assert flag == EPS_POWER_FLAG.LOW_POWER
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc)
        assert flag == EPS_POWER_FLAG.LOW_POWER
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc)
        assert flag == EPS_POWER_FLAG.LOW_POWER
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.EXPERIMENT, soc)
        assert flag == EPS_POWER_FLAG.LOW_POWER

    # Low power entry - low power exit range
    socs = [31, 35, 39]
    for soc in socs:
        # Only casing on low power and nominal states since experiment state EPS logic is not yet finalized
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc)
        assert flag != EPS_POWER_FLAG.LOW_POWER
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc)
        assert flag == EPS_POWER_FLAG.LOW_POWER
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc)
        assert flag != EPS_POWER_FLAG.LOW_POWER

    # Low power exit range and above
    socs = [40, 45, 70, 80, 100]
    for soc in socs:
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NONE, soc)
        assert flag != EPS_POWER_FLAG.LOW_POWER
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.LOW_POWER, soc)
        assert flag != EPS_POWER_FLAG.LOW_POWER
        flag = GET_EPS_POWER_FLAG(EPS_POWER_FLAG.NOMINAL, soc)
        assert flag != EPS_POWER_FLAG.LOW_POWER
