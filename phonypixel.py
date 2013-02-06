import logging
import errno
import socket
import tornado
import time
from uuid import getnode as get_mac

from tornado import ioloop

from packet import DiscoveryPacket, DeviceType

PIXEL_PORT = 9897
MAX_PAYLOAD = 1472
BROADCAST_PORT = 7331

class PhonyPixel(object):
  """Shopped. I can tell from seeing some pushers in my day."""

  def __init__(self, io_loop=None, strips_attached=1, pixels_per_strip=50):
    """Use ioloop if you want multiple IOLoop threads."""

    self.io_loop = io_loop or ioloop.IOLoop.instance()
    self.discovery_packet = self.create_default_descovery_packet(strips_attached=strips_attached,
                                                                 pixels_per_strip=pixels_per_strip)

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) 
    self.socket.setblocking(0)
    self.socket.bind(('', PIXEL_PORT))

    # listen for activity
    self._state = ioloop.IOLoop.ERROR | self.io_loop.READ
    self.io_loop.add_handler(self.socket.fileno(), self._handle_socket_events, self._state)

    # announce 
    self.discovery_timer = tornado.ioloop.PeriodicCallback(self._announce, 971, io_loop=self.io_loop)
    self.discovery_timer.start()

  def _announce(self):
    self.socket.sendto(self.discovery_packet, ('255.255.255.255', BROADCAST_PORT))

  def _handle_socket_events(self, fd, events):
    """This is who the ioloop notifies."""
    try:
      if events & self.io_loop.READ:
        print "HOLY SHIT READ"
        data = self.socket.recv(MAX_PAYLOAD)
        print "DATA: %s" % data
      if not self.socket:
        return
      if events & self.io_loop.ERROR:
        print "HOLY SHIT ERROR"
        self.close()
    except Exception:
      self.close()
      raise

  def close(self):
    self.discovery_timer.stop()
    self.io_loop.remove_handler(self.socket.fileno())
    self.socket.close()
    self.socket = None

  @staticmethod
  def create_default_descovery_packet(version_major=0, version_minor=10, strips_attached=1,
                               pixels_per_strip=50):
    """Pretty close to the actual pixelpusher source"""
    dp = DiscoveryPacket()
    mac_as_int = get_mac()
    mac_address = tuple([(mac_as_int >> ((5-x)*8)) & 0xff for x in xrange(6)])

    # strip_data_size = 1 + pixels_per_strip * 3 * 8 
    # strips_per_packet = int(MTU - (overhead) / strip_data_size)

    max_strips_per_packet = 8; # fixme

    # List of my IPs: socket.gethostbyname_ex(socket.gethostname())[2]
    string_ip_address = socket.gethostbyname(socket.gethostname())
    ip_address= tuple([int(b) for b in string_ip_address.split(".")])

    dp.header.mac_address = mac_address
    dp.header.ip_address

    dp.header.device_type = DeviceType.PIXELPUSHER;
    dp.header.protocol_version = 1;
    dp.header.vendor_id = 2;
    dp.header.product_id = 1;
    dp.header.hw_revision = 2;
    dp.header.sw_revision = version_major * 100 + version_minor;
    dp.header.link_speed = 100000000;
    
    dp.p.pixelpusher.strips_attached = strips_attached;
    dp.p.pixelpusher.max_strips_per_packet = max_strips_per_packet;
    dp.p.pixelpusher.pixels_per_strip = pixels_per_strip;
    dp.p.pixelpusher.update_period = 0xffffffff;  # not measured yet
    dp.p.pixelpusher.power_total = 0;
    return dp

def main():
  phony_pix = PhonyPixel()
  ioloop.IOLoop.instance().start()

if __name__ == "__main__":
  main()