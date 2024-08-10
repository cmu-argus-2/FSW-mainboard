from tasks.imu import Task as imu
from tasks.monitor import Task as monitor
from tasks.obdh import Task as obdh
from tasks.radio_comms import Task as comms
from tasks.sun import Task as sun
from tasks.timing import Task as timing

"""
TODO Copy the state descriptions here


"""

TASK_REGISTRY = {"MONITOR": monitor, "TIMING": timing, "OBDH": obdh, "IMU": imu, "SUN": sun, "COMMS": comms}

TASK_MAPPING_ID = {"MONITOR": 0x05, "TIMING": 0x01, "OBDH": 0x02, "IMU": 0x03, "SUN": 0x11, "COMMS": 0x12}


SM_CONFIGURATION = {
    "STARTUP": {
        "Tasks": {
            "MONITOR": {"Frequency": 1, "Priority": 1},
            "TIMING": {"Frequency": 1, "Priority": 2},
            "OBDH": {"Frequency": 1, "Priority": 3},
        },
        "MovesTo": ["NOMINAL"],
    },
    "NOMINAL": {
        "Tasks": {
            "MONITOR": {"Frequency": 1, "Priority": 1},
            "TIMING": {"Frequency": 1, "Priority": 2},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            "SUN": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            "COMMS": {"Frequency": 0.1, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": ["DOWNLINK", "LOW_POWER", "SAFE"],
    },
    "DOWNLINK": {
        "Tasks": {
            "MONITOR": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 1, "Priority": 3},
            "COMMS": {"Frequency": 0.1, "Priority": 5},
        },
        "MovesTo": ["NOMINAL"],
    },
    "LOW_POWER": {
        "Tasks": {
            "MONITOR": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": ["NOMINAL"],
    },
    "SAFE": {
        "Tasks": {
            "MONITOR": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": ["NOMINAL"],
    },
}
