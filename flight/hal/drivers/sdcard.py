from sys import path

from storage import VfsFat, mount, umount

VFS_MOUNT_POINT = "/sd"


class CustomVfsFat:
    def __init__(self, sd_card):
        self.sd_card = sd_card
        self.vfs = VfsFat(self.sd_card)
        mount(self.vfs, VFS_MOUNT_POINT)
        if VFS_MOUNT_POINT not in path:
            path.append(VFS_MOUNT_POINT)

    def deinit(self):
        self.sd_card.deinit()
        umount(self.vfs)
        return

    def __getattr__(self, name):
        return getattr(self.vfs, name)
