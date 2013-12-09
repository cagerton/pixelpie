import logging
import socket
import struct
import time
import tornado

from packet import PIXEL_PORT

class RemotePixelPusher(object):
  """This lets you schedule periodic pixelpusher updates."""

  def __init__(self, packet, ioloop=None):
    self.packet = packet
    self.mac = self.packet.header.mac_str()
    self.ioloop = ioloop or tornado.ioloop.IOLoop.instance()

    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # initialize to ~50fps
    self.packet_period = 20 # ms
    self.extra_packet_period = 1 #ms
    self.max_packet_period = 100 # ms

    self.seq_number = 0
    self.packet_gen = self._packet_generator()

    ip = packet.header.ip_address

  def strips_per_packet(self):
    # TODO: something like this:
    # return min(int( (packet_mtu - 4) / ( 3 * pixels_per_strip + 1 )), header_value)
    return self.packet.p.pixelpusher.strips_per_packet

  def strips(self):
    return self.packet.p.pixelpusher.strips_attached

  def pixels_per_strip(self):
    return self.packet.p.pixelpusher.pixels_per_strip

  def update_period(self):
    """TODO: normalize time unit?"""
    return self.packet.p.pixelpusher.update_period

  def update_discovery(self, new_packet):
    """Returns the old buffer."""
    logging.info("DiscoveryPacket[%s]- power[%d] update_period[%d] delta_sequence[%d] ip[%s]",
                 new_packet.header.mac_str(),
                 new_packet.p.pixelpusher.power_total,
                 new_packet.p.pixelpusher.update_period,
                 new_packet.p.pixelpusher.delta_sequence,
                 new_packet.header.ip_str())
    old_packet = self.packet
    self.packet = new_packet
    return old_packet

  def pp_addr(self):
    return ("%d.%d.%d.%d" % tuple(self.packet.header.ip_address), PIXEL_PORT)

  def _push_pixels(self):
    """This sends a pixel packet and then reschedules itself."""
    next_packet = self.packet_gen.__next__()
    message = struct.pack("i", self.seq_number) + bytearray(next_packet)
    bytes_sent = self.sock.sendto(message, self.pp_addr())
    self.seq_number += 1

    deadline = time.time() + self.update_period()/1000000.0 + self.extra_packet_period/1000.0
    self.timer = self.ioloop.add_timeout(deadline, self._push_pixels)

  def _packet_generator(self):
    """Returns a generator for packets"""
    self.next_strip = 0
    while(True):
      # TODO: I only have one strip right now.
      yield [self.next_strip] + self.pixel_source(self.next_strip)
      self.next_strip = (self.next_strip + 1) % self.strips()

  # Calls this fxn periodically for pixel data.
  # Adjusts frequency based on strip update time.
  def start_updates_with_source(self, fxn):
    """We will call fxn periodically with strip id as arg."""
    self.pixel_source = fxn
    self._push_pixels()

  def stop_updates(self):
    self.ioloop.remove_timeout(self.timer)


