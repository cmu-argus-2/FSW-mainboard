# Constants and eps-related functions
from core import state_manager as SM
from core.states import STATES
from micropython import const

class EPS_POWER_FLAG:
    NONE = const(0x0)
    LOW_POWER = const(0x1)
    NOMINAL = const(0x2)
    EXPERIMENT = const(0x3)

class EPS_SOC_THRESHOLD:
    LOW_POWER_ENTRY = const(30)
    LOW_POWER_EXIT = const(40)
    EXPERIMENT_ENTRY = const(80)
    EXPERIMENT_EXIT = const(60)

def GET_EPS_POWER_FLAG(curr_flag, soc):
    """ returns current EPS state based on SOC"""
    flag = EPS_POWER_FLAG.NONE
    if (soc <= EPS_SOC_THRESHOLD.LOW_POWER_ENTRY): # below low power threshold
        flag = EPS_POWER_FLAG.LOW_POWER

    elif ((soc > EPS_SOC_THRESHOLD.LOW_POWER_ENTRY)
            and (soc < EPS_SOC_THRESHOLD.LOW_POWER_EXIT)):

        if (curr_flag == EPS_POWER_FLAG.LOW_POWER):
            flag = EPS_POWER_FLAG.LOW_POWER
        else:
            flag = EPS_POWER_FLAG.NOMINAL

    # TODO:
    # add logic to take discharge rate into account
    # when determining experiment state enter/exit thresholds;
    # the current approach is probably too simple
    elif ((soc >= EPS_SOC_THRESHOLD.LOW_POWER_EXIT)
            and (soc < EPS_SOC_THRESHOLD.EXPERIMENT_EXIT)):
        flag = EPS_POWER_FLAG.NOMINAL

    elif ((soc >= EPS_SOC_THRESHOLD.EXPERIMENT_EXIT)
            and (soc <= EPS_SOC_THRESHOLD.EXPERIMENT_ENTRY)):

        if (curr_flag == EPS_POWER_FLAG.EXPERIMENT):
            flag = EPS_POWER_FLAG.EXPERIMENT
        else:
            flag = EPS_POWER_FLAG.NOMINAL

    else:  # greater than experiment entry threshold
        flag = EPS_POWER_FLAG.EXPERIMENT
    return flag