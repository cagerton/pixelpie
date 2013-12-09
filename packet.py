# ctypes for derpbit protocol.

import ctypes
from ctypes import c_uint8, c_uint16, c_uint32

BROADCAST_PORT = 7331
PIXEL_PORT = 9897

class DeviceType():
  ETHERDREAM = 0
  LUMIABRIDGE = 1
  PIXELPUSHER = 2

class DiscoveryPacketHeader(ctypes.Structure):
  _fields_ = [
    ("mac_address", c_uint8 * 6),
    ("ip_address", c_uint8 * 4),
    ("device_type", c_uint8),
    ("protocol_version", c_uint8),
    ("vendor_id", c_uint8),
    ("product_id", c_uint16),
    ("hw_revision", c_uint16),
    ("sw_revision", c_uint16),
    ("link_speed", c_uint32)
  ]
 
  def mac_str(self):
    return "%x%x%x%x%x%x" % tuple(self.mac_address)
 
  def ip_str(self):
    return "%d.%d.%d.%d" % tuple(self.ip_address)

class PixelPusher(ctypes.Structure):
  _fields_ = [
    ('strips_attached', c_uint8),
    ('max_strips_per_packet', c_uint8),
    ('pixels_per_strip', c_uint16),
    ('update_period', c_uint32),   # microseconds
    ('power_total', c_uint32),     # pwm units  
    ('delta_sequence', c_uint32),  # difference between received and expected sequence numbers
    ('controller_ordinal', c_uint32), # ordering number for this controller.
    ('group_ordinal', c_uint32),
    ('artnet_uinverse', c_uint16), # configured artnet starting point for this controller
    ('artnet_channel', c_uint16),
    ('my_port', c_uint16),
    ('strip_flags', c_uint8 * 8), # flags for each strip, for up to eight strips
    ('pusher_flags', c_uint32),
    ('segments', c_uint32),
  ]

class LumiaBridge(ctypes.Structure):
  _fields_ = []

class EtherDream(ctypes.Structure):
  _fields_ = [
    ("buffer_capacity", c_uint16),
    ("max_point_rate", c_uint32),
    ("light_engine_state", c_uint8),
    ("playback_state", c_uint8),
    ("source", c_uint8),
    ("light_engine_flags", c_uint16),
    ("buffer_fullness", c_uint16),
    ("point_rate", c_uint32),
    ("point_count", c_uint32)
  ]

class Particulars(ctypes.Union):
  _fields_ = [
    ("pixelpusher", PixelPusher),
    ("lumiabridge", LumiaBridge),
    ("etherdream", EtherDream)
  ]

class DiscoveryPacket(ctypes.Structure):
  _fields_ = [("header", DiscoveryPacketHeader),
              ("p", Particulars)]
  @classmethod
  def size(cls):
    return ctypes.sizeof(cls)
