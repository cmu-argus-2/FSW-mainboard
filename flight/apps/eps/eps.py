# Constants and eps-related functions
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


# Power threshold in mW
class EPS_POWER_THRESHOLD:
    MAINBOARD = const(1000)  # TODO: this threshold makes sense for v2 mainboards, but change to 400 for v3
    RADIO = const(3300)
    JETSON = const(16000)
    TORQUE_COIL = const(1500)


def GET_EPS_POWER_FLAG(curr_flag, soc):
    """returns current EPS state based on SOC"""
    flag = EPS_POWER_FLAG.NONE
    print(soc)
    if EPS_POWER_FLAG.NONE <= curr_flag <= EPS_POWER_FLAG.EXPERIMENT:
        if 0 <= soc <= EPS_SOC_THRESHOLD.LOW_POWER_ENTRY:  # below low power threshold
            flag = EPS_POWER_FLAG.LOW_POWER

        elif EPS_SOC_THRESHOLD.LOW_POWER_ENTRY < soc < EPS_SOC_THRESHOLD.LOW_POWER_EXIT:
            if curr_flag == EPS_POWER_FLAG.LOW_POWER:
                flag = EPS_POWER_FLAG.LOW_POWER
            else:
                flag = EPS_POWER_FLAG.NOMINAL

        # TODO:
        # add logic to take discharge rate into account
        # when determining experiment state enter/exit thresholds;
        # the current approach is probably too simple
        elif EPS_SOC_THRESHOLD.LOW_POWER_EXIT <= soc < EPS_SOC_THRESHOLD.EXPERIMENT_EXIT:
            flag = EPS_POWER_FLAG.NOMINAL

        elif (soc >= EPS_SOC_THRESHOLD.EXPERIMENT_EXIT) and (soc <= EPS_SOC_THRESHOLD.EXPERIMENT_ENTRY):
            if curr_flag == EPS_POWER_FLAG.EXPERIMENT:
                flag = EPS_POWER_FLAG.EXPERIMENT
            else:
                flag = EPS_POWER_FLAG.NOMINAL

        elif EPS_SOC_THRESHOLD.EXPERIMENT_ENTRY < soc <= 100:  # greater than experiment entry threshold
            flag = EPS_POWER_FLAG.EXPERIMENT

    return flag


def GET_POWER_STATUS(buf, power, threshold, window):
    """returns whether MAV power is above provided threshold"""
    # Add this power value to provided MAV buffer
    buf.append(power)
    # If the length of the buffer is now greater than the window size,
    # Pop the first (oldest) element of the buffer
    if len(buf) > window:
        buf.pop(0)
    # Obtain the moving average
    power_avg = sum(buf) / len(buf)
    # Return the moving average value & the power status
    return (power_avg >= threshold), power_avg
