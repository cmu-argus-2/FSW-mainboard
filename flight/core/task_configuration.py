from core.states import TASK
from tasks.adcs import Task as adcs
from tasks.command import Task as command
from tasks.comms import Task as comms
from tasks.eps import Task as eps
from tasks.gps import Task as gps
from tasks.imu import Task as imu
from tasks.obdh import Task as obdh
from tasks.payload import Task as payload
from tasks.thermal import Task as thermal
from tasks.watchdog import Task as watchdog

TASK_CONFIG = {
    TASK.COMMAND: {"Task": command, "Frequency": 2, "Priority": 1},
    TASK.WATCHDOG: {"Task": watchdog, "Frequency": 1, "Priority": 1},
    TASK.EPS: {"Task": eps, "Frequency": 1, "Priority": 1},
    TASK.OBDH: {"Task": obdh, "Frequency": 0.5, "Priority": 2},
    TASK.COMMS: {"Task": comms, "Frequency": 1, "Priority": 2, "ScheduleLater": True},
    TASK.IMU: {"Task": imu, "Frequency": 5, "Priority": 2, "ScheduleLater": True},
    TASK.ADCS: {"Task": adcs, "Frequency": 5, "Priority": 2, "ScheduleLater": True},
    TASK.THERMAL: {"Task": thermal, "Frequency": 0.1, "Priority": 5, "ScheduleLater": True},
    TASK.GPS: {"Task": gps, "Frequency": 0.03, "Priority": 4, "ScheduleLater": True},
    TASK.PAYLOAD: {"Task": payload, "Frequency": 0.01, "Priority": 4, "ScheduleLater": True},
}
