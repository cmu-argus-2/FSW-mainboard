// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#include "supervisor/board.h"
#include "common-hal/digitalio/DigitalInOut.h"
#include "shared-bindings/digitalio/DigitalInOut.h"

digitalio_digitalinout_obj_t wdt_en;

void board_init(void) {
    wdt_en.base.type = &digitalio_digitalinout_type;
    common_hal_digitalio_digitalinout_construct(&wdt_en, &pin_GPIO15);
    common_hal_digitalio_digitalinout_switch_to_output(&wdt_en, true, DRIVE_MODE_PUSH_PULL);
    common_hal_digitalio_digitalinout_never_reset(&wdt_en);
}

bool board_requests_safe_mode(void) {
    return false;
}

void reset_board(void) {
}

void board_deinit(void) {
}

// Use the MP_WEAK supervisor/shared/board.c versions of routines not defined here.