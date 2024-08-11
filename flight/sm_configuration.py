from tasks.eps import Task as eps
from tasks.imu import Task as imu
from tasks.obdh import Task as obdh
from tasks.radio_comms import Task as comms
from tasks.sun import Task as sun
from tasks.thermal import Task as thermal
from tasks.timing import Task as timing

"""
TODO Copy the state descriptions here


"""

TASK_REGISTRY = {"TIMING": timing, "EPS": eps, "OBDH": obdh, "IMU": imu, "SUN": sun, "COMMS": comms, "THERMAL": thermal}

TASK_MAPPING_ID = {"TIMING": 0x00, "EPS": 0x01, "OBDH": 0x02, "IMU": 0x03, "SUN": 0x11, "COMMS": 0x12, "THERMAL": 0x0A}


SM_CONFIGURATION = {
    "STARTUP": {
        "Tasks": {
            "TIMING": {"Frequency": 1, "Priority": 2},
            "OBDH": {"Frequency": 1, "Priority": 3},
            "EPS": {"Frequency": 1, "Priority": 1},
        },
        "MovesTo": ["NOMINAL"],
    },
    "NOMINAL": {
        "Tasks": {
            "TIMING": {"Frequency": 1, "Priority": 2},
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            "SUN": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            "COMMS": {"Frequency": 0.1, "Priority": 5, "ScheduleLater": True},
            "THERMAL": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": ["DOWNLINK", "LOW_POWER", "SAFE"],
    },
    "DOWNLINK": {
        "Tasks": {
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 1, "Priority": 3},
            "COMMS": {"Frequency": 0.1, "Priority": 5},
            "THERMAL": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": ["NOMINAL"],
    },
    "LOW_POWER": {
        "Tasks": {
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": ["NOMINAL"],
    },
    "SAFE": {
        "Tasks": {
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 1, "Priority": 2},
            "IMU": {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": ["NOMINAL"],
    },
}
