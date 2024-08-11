from core.states import STATES
from micropython import const
from tasks.command import Task as command
from tasks.comms import Task as comms
from tasks.eps import Task as eps
from tasks.imu import Task as imu
from tasks.obdh import Task as obdh
from tasks.sun import Task as sun
from tasks.thermal import Task as thermal
from tasks.timing import Task as timing


class TASK:
    COMMAND = const(0x00)
    TIMING = const(0x01)
    EPS = const(0x02)
    OBDH = const(0x03)
    IMU = const(0x04)
    SUN = const(0x05)
    COMMS = const(0x06)
    THERMAL = const(0x07)


STR_TASKS = ["COMMAND", "TIMING", "EPS", "OBDH", "IMU", "SUN", "COMMS", "THERMAL"]

TASK_REGISTRY = {
    TASK.COMMAND: command,
    TASK.TIMING: timing,
    TASK.EPS: eps,
    TASK.OBDH: obdh,
    TASK.IMU: imu,
    TASK.SUN: sun,
    TASK.COMMS: comms,
    TASK.THERMAL: thermal,
}


SM_CONFIGURATION = {
    STATES.STARTUP: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 1, "Priority": 1},
            TASK.TIMING: {"Frequency": 1, "Priority": 2},
            TASK.OBDH: {"Frequency": 1, "Priority": 3},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
        },
        "MovesTo": [STATES.NOMINAL],
    },
    STATES.NOMINAL: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 1, "Priority": 1},
            TASK.TIMING: {"Frequency": 1, "Priority": 2},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 0.2, "Priority": 2},
            TASK.IMU: {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            TASK.SUN: {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            TASK.COMMS: {"Frequency": 0.1, "Priority": 5, "ScheduleLater": True},
            TASK.THERMAL: {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": [STATES.DOWNLINK, STATES.LOW_POWER, STATES.SAFE],
    },
    STATES.DOWNLINK: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 1, "Priority": 1},
            TASK.TIMING: {"Frequency": 1, "Priority": 2},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 0.2, "Priority": 2},
            TASK.IMU: {"Frequency": 1, "Priority": 3},
            TASK.COMMS: {"Frequency": 0.1, "Priority": 5},
            TASK.THERMAL: {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": [STATES.NOMINAL],
    },
    STATES.LOW_POWER: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 1, "Priority": 1},
            TASK.TIMING: {"Frequency": 1, "Priority": 2},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 0.2, "Priority": 2},
            TASK.IMU: {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": [STATES.NOMINAL, STATES.SAFE],
    },
    STATES.SAFE: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 1, "Priority": 1},
            TASK.TIMING: {"Frequency": 1, "Priority": 2},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 0.2, "Priority": 2},
            TASK.IMU: {"Frequency": 2, "Priority": 3},
        },
        "MovesTo": [STATES.NOMINAL],
    },
}
