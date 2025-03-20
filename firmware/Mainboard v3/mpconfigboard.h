// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2024 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#define MICROPY_HW_BOARD_NAME "Argus3"
#define MICROPY_HW_MCU_NAME "rp2350b"

#define MICROPY_HW_NEOPIXEL (&pin_GPIO0)

#define DEFAULT_I2C_BUS_SDA (&pin_GPIO24)
#define DEFAULT_I2C_BUS_SCL (&pin_GPIO25)

#define DEFAULT_UART_BUS_TX (&pin_GPIO44)
#define DEFAULT_UART_BUS_RX (&pin_GPIO45)

#define DEFAULT_SPI_BUS_SCK  (&pin_GPIO34)
#define DEFAULT_SPI_BUS_MOSI (&pin_GPIO35)
#define DEFAULT_SPI_BUS_MISO (&pin_GPIO32)

// #define CIRCUITPY_PSRAM_CHIP_SELECT (&pin_GPIO47)
