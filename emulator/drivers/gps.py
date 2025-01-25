class GPS:
    def __init__(self, simulator=None) -> None:
        self._nav_data = {}

        self._msg = 0xA8
        self.fix_quality = 3

        self.__simulator = simulator

        self._parsed_data = {
            "message_id": int(self._msg),
            "fix_mode": self.fix_quality,
            "number_of_sv": 0,
            "gps_week": 0,
            "tow": 0,
            "latitude": 0,
            "longitude": 0,
            "ellipsoid_alt": 0,
            "mean_sea_lvl_alt": 0,
            "gdop": 0,
            "pdop": 0,
            "hdop": 0,
            "vdop": 0,
            "tdop": 0,
            "ecef_x": 24161658,  # cm
            "ecef_y": -64844741,
            "ecef_z": 21809692,
            "ecef_vx": 66390526,  # cm/s
            "ecef_vy": 24738890,
            "ecef_vz": -73684928,
        }

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
            self._parsed_data["ecef_x"] = int(ecef_state[0])
            self._parsed_data["ecef_y"] = int(ecef_state[1])
            self._parsed_data["ecef_z"] = int(ecef_state[2])
            self._parsed_data["ecef_vx"] = int(ecef_state[3])
            self._parsed_data["ecef_vy"] = int(ecef_state[4])
            self._parsed_data["ecef_vz"] = int(ecef_state[5])

        return self._parsed_data

    @property
    def parsed_nav_data(self) -> dict:
        return self._parsed_data

    def run_diagnostics(self):
        return []

    def get_flags(self) -> dict:
        return {}

    def enable(self):
        self.__enable = True

    def disable(self):
        self.__enable = False
