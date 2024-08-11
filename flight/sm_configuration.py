from core.states import STATES
from tasks.command import Task as command
from tasks.comms import Task as comms
from tasks.eps import Task as eps
from tasks.imu import Task as imu
from tasks.obdh import Task as obdh
from tasks.sun import Task as sun
from tasks.thermal import Task as thermal
from tasks.timing import Task as timing

TASK_REGISTRY = {
    "COMMAND": command,
    "TIMING": timing,
    "EPS": eps,
    "OBDH": obdh,
    "IMU": imu,
    "SUN": sun,
    "COMMS": comms,
    "THERMAL": thermal,
}
TASK_MAPPING_ID = {
    "COMMAND": 0x00,
    "TIMING": 0x00,
    "EPS": 0x01,
    "OBDH": 0x02,
    "IMU": 0x03,
    "SUN": 0x11,
    "COMMS": 0x12,
    "THERMAL": 0x0A,
}


SM_CONFIGURATION = {
    STATES.STARTUP: {
        "Tasks": {
            "COMMAND": {"Frequency": 1, "Priority": 1},
            "TIMING": {"Frequency": 1, "Priority": 2},
            "OBDH": {"Frequency": 1, "Priority": 3},
            "EPS": {"Frequency": 1, "Priority": 1},
        },
        "MovesTo": [STATES.NOMINAL],
    },
    STATES.NOMINAL: {
        "Tasks": {
            "COMMAND": {"Frequency": 1, "Priority": 1},
            "TIMING": {"Frequency": 1, "Priority": 2},
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 0.2, "Priority": 2},
            "IMU": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            "SUN": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            "COMMS": {"Frequency": 0.1, "Priority": 5, "ScheduleLater": True},
            "THERMAL": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": [STATES.DOWNLINK, STATES.LOW_POWER, STATES.SAFE],
    },
    STATES.DOWNLINK: {
        "Tasks": {
            "COMMAND": {"Frequency": 1, "Priority": 1},
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 0.2, "Priority": 2},
            "IMU": {"Frequency": 1, "Priority": 3},
            "COMMS": {"Frequency": 0.1, "Priority": 5},
            "THERMAL": {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": [STATES.NOMINAL],
    },
    STATES.LOW_POWER: {
        "Tasks": {
            "COMMAND": {"Frequency": 1, "Priority": 1},
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 0.2, "Priority": 2},
            "IMU": {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": [STATES.NOMINAL, STATES.SAFE],
    },
    STATES.SAFE: {
        "Tasks": {
            "COMMAND": {"Frequency": 1, "Priority": 1},
            "EPS": {"Frequency": 1, "Priority": 1},
            "OBDH": {"Frequency": 0.2, "Priority": 2},
            "IMU": {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": [STATES.NOMINAL],
    },
}
