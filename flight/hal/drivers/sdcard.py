from sdcardio import SDCard
from storage import VfsFat


class CustomSDCard:
    def __init__(self, spi, cs, baud):
        self.sd_card = SDCard(spi, cs, baud)

    def deinit(self):
        self.sd_card.cs.deinit()
        self.sd_card.cs = None
        return

    def __getattr__(self, name):
        return getattr(self.sd_card, name)


class CustomVfsFat:
    def __init__(self, sd_card):
        self.vfs = VfsFat(sd_card)

    def deinit(self):
        self.vfs.block_device.deinit()
        return

    def __getattr__(self, name):
        return getattr(self.vfs, name)
