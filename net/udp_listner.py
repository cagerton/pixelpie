from tornado import ioloop
import logging
import socket

class UDPListener(object):
    """Somewhat generic UDP listener boilerplate"""

    def __init__(self, loop=None, state=None):
        logging.debug("%s.__init__ (UDPListener)", self.__class__)

        self.socket = self.open_socket()
        self.loop = loop or ioloop.IOLoop.instance()
        self.add_handlers()

    def add_handlers(self, state=ioloop.IOLoop.ERROR|ioloop.IOLoop.READ):
        self._state = state
        self.loop.add_handler(self.socket.fileno(), self._handle_events, self._state)

    def remove_handlers(self):
        self.loop.remove_handler(self.socket.fileno())

    def _handle_events(self, fd, events):
        """This is who the ioloop notifies."""
        try:
            if events & self.loop.READ:
                self.handle_datagram(fd)
                if not self.socket:
                    return
            if events & self.loop.ERROR:
                self.handle_error(fd)
                if not self.socket:
                    return
            if events & self.loop.WRITE:
                self.handle_write(fd)
        except IOError as e:
            logging.error("Got IOError while handling event")
            self.close()
            raise e

    def close(self):
        self.remove_handlers()
        self.socket.close()
        self.socket = None

    def open_socket(self) -> socket:
        raise NotImplementedError

    def handle_datagram(self, fd):
        raise NotImplementedError

    def handle_write(self, fd):
        raise NotImplementedError

    def handle_error(self, fd):
        logging.error("Got socket error. Closing.")
        self.close()

