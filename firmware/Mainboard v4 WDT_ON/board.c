// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#include "supervisor/board.h"
#include "shared-bindings/microcontroller/Pin.h"
#include "hardware/gpio.h"

#define WDT_EN_PIN 15

void board_init(void) {
    gpio_init(WDT_EN_PIN);
    gpio_set_dir(WDT_EN_PIN, GPIO_OUT);
    gpio_put(WDT_EN_PIN, true);
    common_hal_never_reset_pin(&pin_GPIO15);
}

bool board_requests_safe_mode(void) {
    return false;
}

void reset_board(void) {
    gpio_deinit(WDT_EN_PIN);
    gpio_init(WDT_EN_PIN);
    gpio_set_dir(WDT_EN_PIN, GPIO_OUT);
    gpio_put(WDT_EN_PIN, true);
}

void board_deinit(void) {
}

// Use the MP_WEAK supervisor/shared/board.c versions of routines not defined here.
