from device.pixel import BasicPixel, HighCRIPixel

class Strip(object):
    """Represents a standard strip of RGB Pixels."""

    def __init__(self, length=240):
        self.dirty = False
        self.pixels = [BasicPixel() for _ in range(length)]

    def serialize(self, mark_clean=True):
        """Returns pixel data array. Clears dirty flag unless otherwise advised."""
        if mark_clean:
            self.dirty = False
        return [b for p in self.pixels for b in p.serialize()]


    def dirty(self, value=None):
        """Mark as dirty flag as updated."""
        if value is not None:
            self.dirty = value
        return self.dirty

    def length(self):
        """Returns the LOGICAL number of pixels (not number of packages)"""
        return len(self.pixels)


class HighCRIStrip(Strip):
    """Strip of RGBOW pixels."""

    def __init__(self, length=240):
        """RGBOW strips; length is the number of packages here, not the number of logical pixels. (Sorry)"""
        self.pixels = [HighCRIPixel() for _ in range(int(length / 3))]

