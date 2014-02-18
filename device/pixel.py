from lib.events import EventsMixin, Event
from lib.mixin_utils import MixedClassMeta
class BasicPixel(object):
    """Standard RGB Pixel"""

    def __init__(self):
        self.set_rgb()
        self.value = []

    def serialize(self):
        return self.value

    def set_rgb(self, red=0, green=0, blue=0):
        self.value = [red, green, blue]


class HighCRIPixel(EventsMixin, metaclass=MixedClassMeta):
    """RGB+Orange+White pixel (in three packages)"""
    EventListeners = (
        ('pp.setcolor', 'set_color'),
    )

    def __init__(self):
        self.set_rgbow()
        self.value = []

    def serialize(self):
        return self.value

    def set_rgbow(self, red=0, green=0, blue=0, orange=0, white=0):
        self.value = [ red , green, blue, orange, orange, orange, white, white, white ]

    # TODO: fill this out a bit more...
    def set_color(self, event: Event):
        msg = event.msg
        keys = ('red','green','blue','orange','white')
        val = dict([(k,msg[k]) for k in keys])
        self.set_rgbow(**val)
