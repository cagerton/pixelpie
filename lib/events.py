"""Simple signal bus for listening to & triggering events."""

from datetime import datetime
from tornado import ioloop
import logging
from types import FunctionType


class Event(object):
    """This is an actual event/signal object that gets distributed.

        Note: this could be optimized later into a named tuple instead of a class.
    """
    def __init__(self, name: str, obj=None, msg=None):
        self.timestamp = datetime.now()
        self.name = name
        self.msg = msg
        self.obj = obj


class Listener(object):
    """Represents a callback system."""
    def __init__(self, name: str, action: FunctionType, obj=None, async=True):
        self.name = name
        self.action = action
        self.obj = obj
        self.async = async


class EventBus(object):
    """Listen & respond to events."""
    _inst = None

    @classmethod
    def instance(cls)->'SignalBus':
        if not cls._inst:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        self.signal_root = {}

    def register_listener(self, listener: Listener):
        """Add a listener object to the event bus."""

        if listener.obj not in self.signal_root:
            self.signal_root[listener.obj] = {}
        if listener.name not in self.signal_root[listener.obj]:
            self.signal_root[listener.obj][listener.name] = set()
        self.signal_root[listener.obj][listener.name].add(listener)

    def trigger_signal(self, event: Event):
        """Trigger all event listeners for this event."""
        for root in set([None, event.obj]):
            listeners = self.signal_root.get(root, {}).get(event.name, set())
            for listner in listeners:
                if listner.async:
                    ioloop.IOLoop.current().add_callback(listner.action, event)
                else:
                    listner.action(event)

    def remove_listener(self, listener: Listener):
        """Removes a particular event listener."""

        if listener.name in self.signal_root[listener.obj]:
            self.signal_root[listener.obj][listener.name].remove(listener)

            if len(self.signal_root.get(listener.obj, {}).get(listener.name,[])) == 0:
                del self.signal_root[listener.obj][listener.name]

                if len(self.signal_root[listener.obj]) == 0:
                    del self.signal_root[listener.obj]


class EventsMixin(object):
    """Mix this in to get self.signal(...) method."""

    def __init__(self, *args, **kwargs):
        self._listeners = []
        for name, method in getattr(self.__class__, 'EventListeners', []):
            listener = Listener(name, getattr(self, method))
            EventBus.instance().register_listener(listener)
            self._listeners.append(listener)

    def signal(self, name: str, **kwargs):
        EventBus.instance().trigger_signal(Event(name, **kwargs))

    def stop_events(self):
        for listener in self._listeners:
            EventBus.instance().remove_listener(listener)


class EventHandlerFunction(object):
    """Decorator. Don't use with Methods.
    Example useage:

    @EventHandlerFunction('fire')
    def spray_water(event):
        pass # TODO: spray water on the fire here.
    """

    def __init__(self, name, async=False):
        logging.debug("EventHandler.__call__(%s)", name)
        self.name = name
        self.async = async

    def __call__(self, fx)->FunctionType:
        listener = Listener(self.name, fx, async=self.async)
        EventBus.instance().register_listener(listener)
        return fx
