"""
Satellite State Management

======================

This module defines the operational states for the satellite, represented as constants, along with the corresponding
string representations. Each state indicates a distinct operational mode, with entry and exit criteria.

States:
    STARTUP: Initial state where hardware diagnostics are conducted, and state recovery is performed.
    NOMINAL: Regular operation state following successful diagnostics, or recovery from other states.
    DOWNLINK: Communication state entered upon receiving a ground station signal; telemetry, files, and payload data
                are downlinked according to the ground station requests.
    LOW_POWER: Power-conservation state triggered when battery levels fall below a threshold; resumes nominal upon
                recharge above a recovery threshold.
    SAFE: Emergency state triggered by critical hardware or software failures, allowing for fault handling and
            eventual ground intervention.

Transition functions should be defined based on entry and exit criteria for each state, as outlined in the satellite
state management plan.

Author: Ibrahima S. Sow
"""

from micropython import const


class STATES:
    STARTUP = const(0x00)
    NOMINAL = const(0x01)
    DOWNLINK = const(0x02)
    LOW_POWER = const(0x03)
    SAFE = const(0x04)


STR_STATES = ["STARTUP", "NOMINAL", "DOWNLINK", "LOW_POWER", "SAFE"]


def transition_to_nominal():
    """Transition logic for entering NOMINAL state from various states."""
    # Evaluate conditions to proceed to NOMINAL state
    # Enable necessary devices
    pass


def transition_to_downlink():
    """Transition logic for entering DOWNLINK state."""
    pass


def transition_to_low_power():
    """Transition logic for entering LOW_POWER state."""
    # Initiate power-saving protocols
    # Turn devices to low-power mode configuration
    pass


def transition_to_safe():
    """Transition logic for entering SAFE state."""
    # Handle critical failures and prepare for fault resolution or intervention
    # Run diagnostics
    # Attempt to ecover for critical HW failures if possible --> NVM turn-off (done in appropriate task)
    pass
