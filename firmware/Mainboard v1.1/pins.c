#include "shared-bindings/board/__init__.h"
#include "supervisor/board.h"

static const mp_rom_map_elem_t board_global_dict_table[] = {
    CIRCUITPYTHON_BOARD_DICT_STANDARD_ITEMS

    { MP_ROM_QSTR(MP_QSTR_SCK),       MP_ROM_PTR(&pin_PA13)  },
    { MP_ROM_QSTR(MP_QSTR_MOSI),      MP_ROM_PTR(&pin_PA12)  },
    { MP_ROM_QSTR(MP_QSTR_MISO),      MP_ROM_PTR(&pin_PA14)  },
    { MP_ROM_QSTR(MP_QSTR_SD_CS),     MP_ROM_PTR(&pin_PA27)  },
    { MP_ROM_QSTR(MP_QSTR_UHF_CS),    MP_ROM_PTR(&pin_PB14)  },
    { MP_ROM_QSTR(MP_QSTR_UHF_EN),    MP_ROM_PTR(&pin_PB15)  },

    { MP_ROM_QSTR(MP_QSTR_JETSON_SCK),   MP_ROM_PTR(&pin_PA05)  },
    { MP_ROM_QSTR(MP_QSTR_JETSON_MOSI),  MP_ROM_PTR(&pin_PA04)  },
    { MP_ROM_QSTR(MP_QSTR_JETSON_MISO),  MP_ROM_PTR(&pin_PA06)  },
    { MP_ROM_QSTR(MP_QSTR_JETSON_CS),    MP_ROM_PTR(&pin_PB07)  },
    { MP_ROM_QSTR(MP_QSTR_JETSON_EN),    MP_ROM_PTR(&pin_PB06)  },

    { MP_ROM_QSTR(MP_QSTR_RELAY_A),  MP_ROM_PTR(&pin_PA18)  },
    { MP_ROM_QSTR(MP_QSTR_BURN1),    MP_ROM_PTR(&pin_PA19)  },
    { MP_ROM_QSTR(MP_QSTR_BURN2),    MP_ROM_PTR(&pin_PB16)  },
    { MP_ROM_QSTR(MP_QSTR_BURN3),    MP_ROM_PTR(&pin_PA20)  },
    { MP_ROM_QSTR(MP_QSTR_BURN4),    MP_ROM_PTR(&pin_PA21)  },

    { MP_ROM_QSTR(MP_QSTR_DAC0),     MP_ROM_PTR(&pin_PA02)  },
    { MP_ROM_QSTR(MP_QSTR_A0),       MP_ROM_PTR(&pin_PA02)  },
    { MP_ROM_QSTR(MP_QSTR_A2),       MP_ROM_PTR(&pin_PB08)  },
    { MP_ROM_QSTR(MP_QSTR_A3),       MP_ROM_PTR(&pin_PB09)  },
    { MP_ROM_QSTR(MP_QSTR_BATTERY),  MP_ROM_PTR(&pin_PA07)  },

    { MP_ROM_QSTR(MP_QSTR_VBUS_RST),     MP_ROM_PTR(&pin_PA15)  },
    { MP_ROM_QSTR(MP_QSTR_FUEL_ALRT),    MP_ROM_PTR(&pin_PB31)  },
    { MP_ROM_QSTR(MP_QSTR_CSTAT),        MP_ROM_PTR(&pin_PB00)  },

    { MP_ROM_QSTR(MP_QSTR_PB04),     MP_ROM_PTR(&pin_PB04)  },
    { MP_ROM_QSTR(MP_QSTR_PB05),     MP_ROM_PTR(&pin_PB05)  },
    { MP_ROM_QSTR(MP_QSTR_PB30),     MP_ROM_PTR(&pin_PB30)  },

    { MP_ROM_QSTR(MP_QSTR_GPS_EN),   MP_ROM_PTR(&pin_PB01)  },
    { MP_ROM_QSTR(MP_QSTR_TX),       MP_ROM_PTR(&pin_PB02)  },
    { MP_ROM_QSTR(MP_QSTR_RX),       MP_ROM_PTR(&pin_PB03)  },

    { MP_ROM_QSTR(MP_QSTR_SDA1),     MP_ROM_PTR(&pin_PB12)  },
    { MP_ROM_QSTR(MP_QSTR_SCL1),     MP_ROM_PTR(&pin_PB13)  },
    { MP_ROM_QSTR(MP_QSTR_SDA2),     MP_ROM_PTR(&pin_PA22)  },
    { MP_ROM_QSTR(MP_QSTR_SCL2),     MP_ROM_PTR(&pin_PA23)  },
    { MP_ROM_QSTR(MP_QSTR_SDA3),     MP_ROM_PTR(&pin_PA16)  },
    { MP_ROM_QSTR(MP_QSTR_SCL3),     MP_ROM_PTR(&pin_PA17)  },

    { MP_ROM_QSTR(MP_QSTR_WDT_EN),   MP_ROM_PTR(&pin_PB22)  },
    { MP_ROM_QSTR(MP_QSTR_WDT_WDI),  MP_ROM_PTR(&pin_PB23)  },
    { MP_ROM_QSTR(MP_QSTR_NEOPIXEL), MP_ROM_PTR(&pin_PB17)  },

    { MP_ROM_QSTR(MP_QSTR_UART), MP_ROM_PTR(&board_uart_obj) },
    { MP_ROM_QSTR(MP_QSTR_I2C),  MP_ROM_PTR(&board_i2c_obj)  },
    { MP_ROM_QSTR(MP_QSTR_SPI),  MP_ROM_PTR(&board_spi_obj)  },
};
MP_DEFINE_CONST_DICT(board_module_globals, board_global_dict_table);
