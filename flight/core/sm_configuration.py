from core.states import STATES, TASK
from tasks.adcs import Task as adcs
from tasks.command import Task as command
from tasks.comms import Task as comms
from tasks.eps import Task as eps
from tasks.gps import Task as gps
from tasks.imu import Task as imu
from tasks.obdh import Task as obdh
from tasks.telemetry import Task as telemetry
from tasks.thermal import Task as thermal

TASK_REGISTRY = {
    TASK.COMMAND: command,
    TASK.EPS: eps,
    TASK.OBDH: obdh,
    TASK.ADCS: adcs,
    TASK.IMU: imu,
    TASK.COMMS: comms,
    TASK.THERMAL: thermal,
    TASK.GPS: gps,
    TASK.TM: telemetry,
}

SM_CONFIGURATION = {
    STATES.STARTUP: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 1, "Priority": 3},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
        },
        "MovesTo": [STATES.NOMINAL],
    },
    STATES.NOMINAL: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 10, "Priority": 1},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 1, "Priority": 2},
            TASK.IMU: {"Frequency": 10, "Priority": 5},
            TASK.ADCS: {"Frequency": 1, "Priority": 2, "ScheduleLater": True},
            TASK.COMMS: {"Frequency": 1, "Priority": 2, "ScheduleLater": True},
            TASK.THERMAL: {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            TASK.GPS: {"Frequency": 0.5, "Priority": 5, "ScheduleLater": True},
            TASK.TM: {"Frequency": 1, "Priority": 4, "ScheduleLater": True},
        },
        "MovesTo": [STATES.DOWNLINK, STATES.LOW_POWER, STATES.SAFE],
    },
    STATES.DOWNLINK: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 10, "Priority": 1},
            TASK.COMMS: {"Frequency": 5, "Priority": 1},
            TASK.TM: {"Frequency": 1, "Priority": 1},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 1, "Priority": 2},
            TASK.IMU: {"Frequency": 1, "Priority": 3},
            TASK.ADCS: {"Frequency": 1, "Priority": 2, "ScheduleLater": True},
            TASK.THERMAL: {"Frequency": 1, "Priority": 5, "ScheduleLater": True},
            TASK.GPS: {"Frequency": 0.2, "Priority": 5, "ScheduleLater": True},
        },
        "MovesTo": [STATES.NOMINAL, STATES.SAFE],
    },
    STATES.LOW_POWER: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 10, "Priority": 1},
            TASK.COMMS: {"Frequency": 1, "Priority": 1},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 1, "Priority": 2},
            TASK.IMU: {"Frequency": 2, "Priority": 3},
            TASK.ADCS: {"Frequency": 1, "Priority": 2, "ScheduleLater": True},
        },
        "MovesTo": [STATES.NOMINAL, STATES.SAFE],
    },
    STATES.SAFE: {
        "Tasks": {
            TASK.COMMAND: {"Frequency": 10, "Priority": 1},
            TASK.COMMS: {"Frequency": 5, "Priority": 1},
            TASK.EPS: {"Frequency": 1, "Priority": 1},
            TASK.OBDH: {"Frequency": 0.2, "Priority": 2},
            TASK.IMU: {"Frequency": 2, "Priority": 3},
            TASK.ADCS: {"Frequency": 1, "Priority": 2, "ScheduleLater": True},
        },
        "MovesTo": [STATES.NOMINAL],
    },
}
