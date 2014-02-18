__author__ = 'cda'
import logging

from lib.events import EventsMixin, EventBus, Listener, Event, EventHandlerFunction
from lib.mixin_utils import MixedClassMeta

from tornado import ioloop
from tornado import websocket
import tornado
import tornado.httpserver
import tornado.web

from net.listen_util import PusherIndex

from tornado import websocket
import json


logging.basicConfig(level=logging.DEBUG)

class PusherWebSocket(EventsMixin,
                      websocket.WebSocketHandler,
                      metaclass=MixedClassMeta):
    """Handles pushing data to web browser.
        Handles emiting control events."""

    OPEN = 0
    CLOSED = 1

    EventListeners = (('pp.update', 'pusher_state_update'),)

    def __init__(self, *args, **kwargs):
        logging.info("PusherWebSocket __init__. args:%s, kwargs:%s", str(args), str(kwargs))

    def open(self):
        logging.info("New WS connection.")
        self.signal('ws.open', obj=self)
        self.state = self.OPEN

    def on_message(self, message):
        try:
            msg = json.loads(message)
        except Exception as e:
            logging.exception(e)
            self.close()
        self.signal('pp.setcolor', obj=msg['mac'], msg=msg)


    def on_close(self):
        self.state = self.CLOSED
        self.stop_events()
        logging.info("Closed WS connection.")


    def pusher_state_update(self, event: Event):
        if self.state == self.CLOSED:
            return
        pusher = event.obj
        data = json.dumps({'type': 'update', 'data': {pusher.mac: pusher.conf}})
        self.write_message(data)



if __name__ == '__main__':
    # Setup logging for the signal bus
    l = Listener('ws.open', lambda x:logging.error("open signal!"))
    EventBus.instance().register_listener(l)

    # listen for udp broadcasts & keep track of pushers.
    pusher_index = PusherIndex()

    # Setup web application
    application = tornado.web.Application([
        (r'/ws', PusherWebSocket),
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)

    logging.info("setting up taskloop")
    loop = ioloop.IOLoop.instance()
    loop.instance().start()
