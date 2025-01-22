"""
Satellite State Management

======================

This module defines the operational states for the satellite, represented as constants, along with the corresponding
string representations. Each state indicates a distinct operational mode, with entry and exit criteria.

States:
    STARTUP: The initial state where hardware boot, diagnostics, and state recovery are performed.
    Burnwires are activated at the end of this phase.
    DETUMBLING: A state where the satellite reduces its angular momentum below a defined threshold.
    This state is active until stability is achieved or a timeout occurs.
    NOMINAL: The primary operational state where all systems, excluding payload, are fully functional,
    provided sufficient power levels are maintained.
    EXPERIMENT: This state is similar to NOMINAL with the activation of the Payload (OD). Given the high
    power draw, this state requires a high state of charge for opportunistic transitions.
    LOW_POWER: A power-conservation state entered when battery levels drop below a critical threshold.
    Non-essential systems are turned off, and the satellite resumes nominal operations upon recharging above a
    recovery threshold.

Author: Ibrahima S. Sow
"""

from micropython import const


class TASK:
    COMMAND = const(0x00)
    WATCHDOG = const(0x01)
    EPS = const(0x02)
    OBDH = const(0x03)
    COMMS = const(0x04)
    IMU = const(0x05)
    ADCS = const(0x06)
    THERMAL = const(0x07)
    GPS = const(0x08)
    PAYLOAD = const(0x09)


class STATES:
    STARTUP = const(0x00)
    DETUMBLING = const(0x01)
    NOMINAL = const(0x02)
    EXPERIMENT = const(0x03)
    LOW_POWER = const(0x04)

    TRANSITIONS = {
        STARTUP: [DETUMBLING],
        DETUMBLING: [NOMINAL, LOW_POWER],
        NOMINAL: [LOW_POWER, DETUMBLING, EXPERIMENT],
        EXPERIMENT: [NOMINAL],
        LOW_POWER: [NOMINAL, LOW_POWER],
    }

    DETUMBLING_TIMEOUT_DURATION = 15  # seconds - TODO: Update with actual value


STR_STATES = ["STARTUP", "DETUMBLING", "NOMINAL", "LOW_POWER", "EXPERIMENT"]
