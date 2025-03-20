// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2024 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#include "shared-bindings/board/__init__.h"

static const mp_rom_map_elem_t board_module_globals_table[] = {
    CIRCUITPYTHON_BOARD_DICT_STANDARD_ITEMS

    { MP_ROM_QSTR(MP_QSTR_NEOPIXEL),    MP_ROM_PTR(&pin_GPIO0) },
    { MP_ROM_QSTR(MP_QSTR_COIL_EN),    MP_ROM_PTR(&pin_GPIO1) },
    { MP_ROM_QSTR(MP_QSTR_WDT_WDI),    MP_ROM_PTR(&pin_GPIO2) },
    { MP_ROM_QSTR(MP_QSTR_BATT_ALRT),    MP_ROM_PTR(&pin_GPIO3) },

    { MP_ROM_QSTR(MP_QSTR_HEAT0_ON),    MP_ROM_PTR(&pin_GPIO4) },
    { MP_ROM_QSTR(MP_QSTR_HEAT1_ON),    MP_ROM_PTR(&pin_GPIO5) },
    { MP_ROM_QSTR(MP_QSTR_HEAT_EN),    MP_ROM_PTR(&pin_GPIO6) },

    { MP_ROM_QSTR(MP_QSTR_JETSON_EN),     MP_ROM_PTR(&pin_GPIO7) },
    { MP_ROM_QSTR(MP_QSTR_TX1),     MP_ROM_PTR(&pin_GPIO8) },
    { MP_ROM_QSTR(MP_QSTR_RX1),     MP_ROM_PTR(&pin_GPIO9) },

    { MP_ROM_QSTR(MP_QSTR_CLK1),     MP_ROM_PTR(&pin_GPIO10) },
    { MP_ROM_QSTR(MP_QSTR_MOSI1),    MP_ROM_PTR(&pin_GPIO11) },
    { MP_ROM_QSTR(MP_QSTR_MISO1),     MP_ROM_PTR(&pin_GPIO12) },

    { MP_ROM_QSTR(MP_QSTR_SD_CS),    MP_ROM_PTR(&pin_GPIO13) },
    { MP_ROM_QSTR(MP_QSTR_WDT_EN),     MP_ROM_PTR(&pin_GPIO15) },

    { MP_ROM_QSTR(MP_QSTR_PAYLOAD_IO2),    MP_ROM_PTR(&pin_GPIO16) },
    { MP_ROM_QSTR(MP_QSTR_PAYLOAD_IO1),  MP_ROM_PTR(&pin_GPIO17) },
    { MP_ROM_QSTR(MP_QSTR_PAYLOAD_IO0),     MP_ROM_PTR(&pin_GPIO18) },

    { MP_ROM_QSTR(MP_QSTR_LORA_nRST),  MP_ROM_PTR(&pin_GPIO19) },
    { MP_ROM_QSTR(MP_QSTR_LORA_BUSY),    MP_ROM_PTR(&pin_GPIO20) },
    { MP_ROM_QSTR(MP_QSTR_LORA_INT),     MP_ROM_PTR(&pin_GPIO21) },
    { MP_ROM_QSTR(MP_QSTR_LORA_RX_EN),     MP_ROM_PTR(&pin_GPIO22) },
    { MP_ROM_QSTR(MP_QSTR_LORA_TX_EN),   MP_ROM_PTR(&pin_GPIO23) },
    
    { MP_ROM_QSTR(MP_QSTR_SDA0),  MP_ROM_PTR(&pin_GPIO24) },
    { MP_ROM_QSTR(MP_QSTR_SCL0),  MP_ROM_PTR(&pin_GPIO25) },

    { MP_ROM_QSTR(MP_QSTR_PAYLOAD_nCS),  MP_ROM_PTR(&pin_GPIO28) },
    { MP_ROM_QSTR(MP_QSTR_PAYLOAD_EN),  MP_ROM_PTR(&pin_GPIO29) },
    { MP_ROM_QSTR(MP_QSTR_PAYLOAD_FLT),  MP_ROM_PTR(&pin_GPIO30) },

    { MP_ROM_QSTR(MP_QSTR_RW_EN),  MP_ROM_PTR(&pin_GPIO31) },

    { MP_ROM_QSTR(MP_QSTR_MISO0),  MP_ROM_PTR(&pin_GPIO32) },

    { MP_ROM_QSTR(MP_QSTR_LORA_nCS),  MP_ROM_PTR(&pin_GPIO33) },

    { MP_ROM_QSTR(MP_QSTR_CLK0),  MP_ROM_PTR(&pin_GPIO34) },
    { MP_ROM_QSTR(MP_QSTR_MOSI0),  MP_ROM_PTR(&pin_GPIO35) },

    { MP_ROM_QSTR(MP_QSTR_LORA_EN),  MP_ROM_PTR(&pin_GPIO36) },
    { MP_ROM_QSTR(MP_QSTR_LORA_FLT),  MP_ROM_PTR(&pin_GPIO37) },

    { MP_ROM_QSTR(MP_QSTR_GPS_EN),  MP_ROM_PTR(&pin_GPIO38) },
    { MP_ROM_QSTR(MP_QSTR_GPS_FLT),  MP_ROM_PTR(&pin_GPIO39) },

    { MP_ROM_QSTR(MP_QSTR_3V3P_FLT),  MP_ROM_PTR(&pin_GPIO41) },
    { MP_ROM_QSTR(MP_QSTR_3V3P_EN),  MP_ROM_PTR(&pin_GPIO42) },
    { MP_ROM_QSTR(MP_QSTR_3V3M_RST),  MP_ROM_PTR(&pin_GPIO43) },

    { MP_ROM_QSTR(MP_QSTR_TX0),  MP_ROM_PTR(&pin_GPIO44) },
    { MP_ROM_QSTR(MP_QSTR_RX0),  MP_ROM_PTR(&pin_GPIO45) },

    { MP_ROM_QSTR(MP_QSTR_SDA1),    MP_ROM_PTR(&pin_GPIO46) },
    { MP_ROM_QSTR(MP_QSTR_SCL1),    MP_ROM_PTR(&pin_GPIO47) },

    { MP_ROM_QSTR(MP_QSTR_I2C),     MP_ROM_PTR(&board_i2c_obj)  },
    { MP_ROM_QSTR(MP_QSTR_SPI),     MP_ROM_PTR(&board_spi_obj)  },
    { MP_ROM_QSTR(MP_QSTR_UART),    MP_ROM_PTR(&board_uart_obj) },
};
MP_DEFINE_CONST_DICT(board_module_globals, board_module_globals_table);
