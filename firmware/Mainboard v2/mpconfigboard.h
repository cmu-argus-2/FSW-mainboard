#pragma once

#define MICROPY_HW_BOARD_NAME "Argus2"
#define MICROPY_HW_MCU_NAME "rp2040"

//#define MICROPY_HW_LED_STATUS (&pin_GPIO25)

//#define MICROPY_HW_NEOPIXEL (&pin_GPIO17)

#define DEFAULT_I2C_BUS_SDA (&pin_GPIO0)
#define DEFAULT_I2C_BUS_SCL (&pin_GPIO1)

#define DEFAULT_UART_BUS_TX (&pin_GPIO12)
#define DEFAULT_UART_BUS_RX (&pin_GPIO13)

#define DEFAULT_SPI_BUS_SCK  (&pin_GPIO18)
#define DEFAULT_SPI_BUS_MOSI (&pin_GPIO19)
#define DEFAULT_SPI_BUS_MISO (&pin_GPIO16)