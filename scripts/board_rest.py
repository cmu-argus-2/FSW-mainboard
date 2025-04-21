import microcontroller

# go into bootloader mode
microcontroller.on_next_reset(microcontroller.BOOTLOADER)

microcontroller.reset()
