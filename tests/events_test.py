import logging

from datetime import timedelta
from tornado.testing import AsyncTestCase, gen_test
from tornado import gen

from lib.events import Event, EventBus, Listener, EventsMixin
from lib.mixin_utils import MixedClassMeta

logging.basicConfig(level=logging.DEBUG)


class TestClass(EventsMixin, metaclass=MixedClassMeta):

    EventListeners = (
        ('test.event', 'foobar'),
    )
    def __init__(self):
        self.observed = 0

    def foobar(self, event):
        self.observed += 1

    def ping(self):
        self.signal('test.event')



class SignalsTest(AsyncTestCase):

    def setUp(self):
        self.bus = EventBus()
        super().setUp()

    @gen_test(timeout=0.2)
    def test_basic_signal(self):
        res = []
        hit = lambda x: res.append(True)
        listener = Listener('pp.found', hit, async=False)

        res2 = []
        hit2 = lambda x: res2.append(True)
        listener2 = Listener('pp.found', hit2, async=True)

        self.bus.register_listener(listener)
        self.bus.register_listener(listener2)

        self.assertEqual(len(res), 0)
        signal = Event('pp.something-else')

        self.bus.trigger_signal(signal)
        self.assertEqual(len(res), 0)

        signal = Event('pp.found')
        self.bus.trigger_signal(signal)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res2), 0)
        yield gen.Task(self.io_loop.current().add_timeout, timedelta(milliseconds=2))
        self.assertEqual(len(res2), 1)

    def test_with_obj(self):
        obj = 1
        res = []
        hit = lambda x: res.append(True)
        signal = Event('pp', obj=obj)
        listener = Listener('pp', hit, obj=obj, async=False)

        obj2='foo'
        res2 = []
        hit2 = lambda x: res2.append(True)
        signal2 = Event('pp', obj=obj2)
        listener2 = Listener('pp', hit2, obj=obj2,  async=False)

        self.bus.register_listener(listener)
        self.bus.register_listener(listener2)

        self.bus.trigger_signal(signal)
        self.bus.trigger_signal(signal2)

        self.assertEqual(len(res), 1)
        self.assertEqual(len(res2), 1)

    def test_removal(self):
        res = []
        hit = lambda x:res.append(True)
        listener = Listener('pp.found', hit, async=False)
        self.bus.register_listener(listener)
        signal = Event('pp.found')
        self.bus.trigger_signal(signal)
        self.bus.remove_listener(listener)
        self.assertEqual(len(res), 1)
        self.bus.trigger_signal(signal)
        self.assertEqual(len(res), 1)

    @gen_test(timeout=0.2)
    def test_basic_mixin_and_decorator(self):
        tc = TestClass()
        self.assertEqual(tc.observed, 0)
        tc.ping()

        yield gen.Task(self.io_loop.current().add_timeout, timedelta(milliseconds=2))
        self.assertEqual(tc.observed, 1)



if __name__ == '__main__':
    import tornado.testing
    tornado.testing.main()