"""
Shared orbit reference state for ADCS propagation.

Values are uplinked from GS through the UPLINK_ORBIT_REFERENCE command.
Units:
- time_reference: s (uint32)
- position: cm (int32)
- velocity: cm/s (int32)
"""

_orbit_reference = {
    "time_reference": 0,
    "pos_x": 0,
    "pos_y": 0,
    "pos_z": 0,
    "vel_x": 0,
    "vel_y": 0,
    "vel_z": 0,
}


def set_orbit_reference(time_reference, pos_x, pos_y, pos_z, vel_x, vel_y, vel_z):
    _orbit_reference["time_reference"] = int(time_reference)
    _orbit_reference["pos_x"] = int(pos_x)
    _orbit_reference["pos_y"] = int(pos_y)
    _orbit_reference["pos_z"] = int(pos_z)
    _orbit_reference["vel_x"] = int(vel_x)
    _orbit_reference["vel_y"] = int(vel_y)
    _orbit_reference["vel_z"] = int(vel_z)


def get_orbit_reference():
    # Return a copy to avoid accidental mutation by callers.
    return dict(_orbit_reference)
