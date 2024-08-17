"""driver_exceptions.py: Contains exceptions for the HAL drivers

This file contains the exceptions for the HAL drivers

Author: Harry Rosmann
"""


class gps_fatal_exception(Exception):
    """gps_fatal_exception: Exception for fatal GPS errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class battery_power_monitor_fatal_exception(Exception):
    """battery_power_monitor_fatal_exception: Exception for fatal battery power monitor errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class jetson_power_monitor_fatal_exception(Exception):
    """jetson_power_monitor_fatal_exception: Exception for fatal Jetson monitor errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class imu_fatal_exception(Exception):
    """imu_fatal_exception: Exception for fatal IMU errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class charger_fatal_exception(Exception):
    """charger_fatal_exception: Exception for fatal charger errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class torque_xp_fatal_exception(Exception):
    """torque_xp_fatal_exception: Exception for fatal torque driver in the x+ direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class torque_xm_fatal_exception(Exception):
    """torque_xm_fatal_exception: Exception for fatal torque driver in the x- direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class torque_yp_fatal_exception(Exception):
    """torque_yp_fatal_exception: Exception for fatal torque driver in the y+ direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class torque_ym_fatal_exception(Exception):
    """torque_ym_fatal_exception: Exception for fatal torque driver in the y- direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class torque_z_fatal_exception(Exception):
    """torque_z_fatal_exception: Exception for fatal torque driver in the z direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class light_sensor_xp_fatal_exception(Exception):
    """light_sensor_xp_fatal_exception: Exception for fatal light sensor in the x+ direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class light_sensor_xm_fatal_exception(Exception):
    """light_sensor_xm_fatal_exception: Exception for fatal light sensor in the x- direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class light_sensor_yp_fatal_exception(Exception):
    """light_sensor_yp_fatal_exception: Exception for fatal light sensor in the y+ direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class light_sensor_ym_fatal_exception(Exception):
    """light_sensor_ym_fatal_exception: Exception for fatal light sensor in the y- direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class light_sensor_zm_fatal_exception(Exception):
    """light_sensor_z_fatal_exception: Exception for fatal light sensor in the z direction errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class rtc_fatal_exception(Exception):
    """rtc_fatal_exception: Exception for fatal RTC errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class radio_fatal_exception(Exception):
    """radio_fatal_exception: Exception for fatal radio errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class burn_wire_fatal_exception(Exception):
    """burn_wire_fatal_exception: Exception for fatal burn wire errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class jetson_fatal_exception(Exception):
    """jetson_fatal_exception: Exception for fatal Jetson errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class vfs_fatal_exception(Exception):
    """vfs_fatal_exception: Exception for fatal VFS errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class payload_uart_fatal_exception(Exception):
    """payload_uart_fatal_exception: Exception for fatal payload uart errors"""

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"
