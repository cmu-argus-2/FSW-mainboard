class GPS:
    def __init__(self, simulator=None) -> None:
        self._nav_data = {}

        self._msg = 0xA8
        self.fix_quality = 3

        self.__simulator = simulator

        # GPS data fields
        self.unix_time = 0
        self.message_id = int(self._msg)
        self.fix_mode = self.fix_quality
        self.number_of_sv = 0
        self.week = 0
        self.tow = 0
        self.latitude = 0
        self.longitude = 0
        self.ellipsoid_altitude = 0
        self.mean_sea_level_altitude = 0
        self.gdop = 0
        self.pdop = 0
        self.hdop = 0
        self.vdop = 0
        self.tdop = 0
        self.ecef_x = 24161658
        self.ecef_y = -64844741
        self.ecef_z = 21809692
        self.ecef_vx = 66390526
        self.ecef_vy = 24738890
        self.ecef_vz = -73684928

    def has_fix(self):
        """True if a current fix for location information is available."""
        return self.fix_quality is not None and self.fix_quality >= 1

    def update(self) -> bool:
        # self._msg = 0xA8
        _ = self.parse_data()
        return True

    def parse_data(self) -> dict:
        if self.__simulator:
            # Simualte all other fields
            ecef_state = self.__simulator.gps()
            self.unix_time = int(ecef_state[0])
            self.ecef_x = int(ecef_state[1])
            self.ecef_y = int(ecef_state[2])
            self.ecef_z = int(ecef_state[3])
            self.ecef_vx = int(ecef_state[4])
            self.ecef_vy = int(ecef_state[5])
            self.ecef_vz = int(ecef_state[6])

    def run_diagnostics(self):
        return []

    def get_flags(self) -> dict:
        return {}

    def enable(self):
        self.__enable = True

    def disable(self):
        self.__enable = False
