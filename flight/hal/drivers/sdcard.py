from sdcardio import SDCard
from storage import VfsFat


class CustomSDCard(SDCard):
    def __init__(self, spi, cs, baud):
        self.sd_card = SDCard(spi, cs, baud)

    def deinit(self):
        self.cs.deinit()
        self.cs = None
        return

    def __getattr__(self, name):
        return getattr(self.sd_card, name)


class CustomVfsFat(VfsFat):
    def __init__(self, sd_card):
        self.vfs = VfsFat(sd_card)

    def deinit(self):
        self.vfs.block_device.deinit()
        return

    def __getattr__(self, name):
        return getattr(self.vfs, name)
