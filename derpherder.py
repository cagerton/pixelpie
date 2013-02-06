from __future__ import print_function

import errno
import logging
import socket
import time

from tornado import ioloop

from packet import DiscoveryPacket
from pusher import RemotePixelPusher

BROADCAST_HOST = ''
BROADCAST_PORT = 7331
PP_LISTEN_PORT = 9897

# DerpHerder is the discovery protocol listener for PixelPusher devices.

class DerpHerder(object):
  """It's your python powered photon delivery driver hookup connection machine!"""

  class TimeoutNode():
    """To help keep track of the really slow ones..."""
    def __init__(self, item, timestamp):
      self.item = item
      self.timestamp = timestamp
      self.prev = None
      self.next = None

  def __init__(self, existing_socket=None, io_loop=None, timeout=3):
    """Specify timeout=None to turn off expire/timeout system."""
    logging.info("Yo dawg, I heard you like derps...")

    self.devices = {}
    self.spare_buffer = DiscoveryPacket()

    # Keep track of things:
    self.timeout = timeout
    self.timeout_head = None # last seen longest ago
    self.timeout_tail = None # seen most recently
    self.timeout_map = dict()

    # Who we should notify:
    self.found_callbacks = set()
    self.lost_callbacks = set()

    # Listen socket:
    self.socket = existing_socket or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) 
    self.socket.bind((BROADCAST_HOST, BROADCAST_PORT))

    # IOLoop:
    self.io_loop = io_loop or ioloop.IOLoop.instance()
    self._state = ioloop.IOLoop.ERROR | self.io_loop.READ
    self.io_loop.add_handler(self.socket.fileno(), self._handle_socket_events, self._state)

    # Handle timeouts:
    if timeout is not None:
      self.timer = ioloop.PeriodicCallback(self._expire_devices, 599, io_loop=self.io_loop)
      self.timer.start()

  def add_callbacks(self, found=None, lost=None):
    """I find your pixels alluring and wish to subscribe to your newsletter."""
    if found:
      self.found_callbacks.add(found)
    if lost:
      self.lost_callbacks.add(lost)

  def remove_callback(self, callback):
    """You unfriended me on Facebook"""
    del self.found_callbacks[callback]
    del self.lost_callbacks[callback]

  def _expire_devices(self):
    """Raise your hand if you get disconnected. (only used if timeout is not None)"""
    now = time.time()
    head = self.timeout_head
    while(head and head.timestamp + self.timeout < now):
      del self.timeout_map[head.item]
      del self.devices[head.item.mac]
      for callback in self.lost_callbacks:
        callback(head.item)
      head = head.next
    self.timeout_head = head
    if(head is None):
      self.timeout_tail = None

  def close(self):
    """Turn off [light] socket."""
    self.timer.stop()
    self.io_loop.remove_handler(self.socket.fileno())
    self.socket.close()
    self.socket = None

  def _handle_socket_events(self, fd, events):
    """This is who the ioloop notifies."""
    try:
      if events & self.io_loop.READ:
        self._handle_read()
      if not self.socket:
        return
      if events & self.io_loop.ERROR:
        logging.error("Got some kind of IO Error. WTF?")
        self.close()
    except Exception:
      self.close()
      raise

  def _handle_read(self):
    """Sometimes a parrot talks. HELLO. HELLO. HELLO. HELLO."""
    packet_buffer = self.spare_buffer
    self.socket.recv_into(packet_buffer, packet_buffer.size())
    mac = packet_buffer.header.mac_str()
    if (mac in self.devices):
      device = self.devices[mac]
      self.spare_buffer = device.update_discovery(packet_buffer)
    else:
      device = RemotePixelPusher(packet_buffer)
      self.spare_buffer = DiscoveryPacket()
      self.devices[mac] = device
      for callback in self.found_callbacks:
        callback(device)
    self.touch_device(device)      

  def touch_device(self, device):
    """Mark device as seen / back to the end of the timeout line."""
    now = time.time()
    if(device in self.timeout_map):
      node = self.timeout_map[device]
      node.timestamp = now
      if node.prev:
        node.prev.next = node.next
      else:
        self.timeout_head = node.next
      if(node.next):
        node.next.prev = node.prev
    else:
      node = self.TimeoutNode(device, now)
      self.timeout_map[device] = node
    if(self.timeout_tail is None):
      self.timeout_head = node
    else:
      self.timeout_tail.next = node
      node.prev = self.timeout_tail

def main():
  found_fxn = lambda x: print("Found a new device! %s  -  %s" % (x.packet.header.mac_str(), x.packet.header.ip_str()))
  lost_fxn =  lambda x: print("We seem to have lost the device: %s" % x.packet.header.ip_str())

  logging.basicConfig(level=logging.INFO)
  logging.info("Starting bare device discovery demo.")

  d = DerpHerder()
  d.add_callbacks(found=found_fxn, lost=lost_fxn)

  ioloop.IOLoop.instance().start()


if __name__ == "__main__":
  main()
