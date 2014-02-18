from datetime import datetime, timedelta
from tornado import ioloop
import logging
import struct
from tornado.gen import coroutine, Task
import socket

from device.discovery import DiscoveryPacket, PP_Flags
from device.strip import Strip, HighCRIStrip


ConfigParams = ('strips_attached',
                  'max_strips_per_packet',
                  'controller_ordinal',
                  'group_ordinal',
                  'my_port',
                  'pusher_flags',
                  'segments')


class Pusher(object):
    """Represents one remote pusher unit."""

    def __init__(self, loop=None):
        self.last_packet = DiscoveryPacket()
        self.loop = loop or ioloop.IOLoop.instance()
        self.conf = {}
        self.strips = []
        self.last_push = datetime.now()
        self.first_seen = None
        self.last_seen = None
        self.seq = int(0)
        self.mac = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pp_addr = None

    def update_discovery(self, packet:DiscoveryPacket, timestamp=None):
        """Updates / initializes a pusher object with a discovery packet.
           returns an old discovery packet for recycling.
        """
        self.last_seen = timestamp or datetime.now()

        old_packet = self.last_packet
        self.last_packet = packet

        if not self.first_seen:
            self.first_seen = self.last_seen
            self.setup_strips()
        else:
            self.check_feedback()

        return old_packet

    def check_feedback(self):
        params = self.last_packet.p.pixelpusher
        update = params.update_period
        delta = params.delta_sequence
        power = params.power_total

        logging.info("pp %s   update_period: %d,  delta_sequence: %d,  power_total: %d",
                     self.mac, update, delta, power)

    def setup_strips(self):
        """Pull pusher config from last discovery packet & initialize strips."""
        self.mac = self.last_packet.header.mac_str()
        particulars = self.last_packet.p.pixelpusher

        for k in ConfigParams:
            self.conf[k] = int(getattr(particulars, k))
        self.conf['flags'] = [int(x) for x in particulars.strip_flags]

        for i in range(min(8, self.conf['strips_attached'])):
            if self.conf['flags'][i] & PP_Flags.RGBOW:
                self.strips.append(HighCRIStrip())
            else:
                self.strips.append(Strip())

        self.pp_addr = (self.last_packet.header.ip_str(), self.conf['my_port'])
        self.loop.add_callback(self.scheduler)

    def next_tick(self):
        """Return a good time to push the next packet."""
        period = timedelta(microseconds=self.last_packet.p.pixelpusher.update_period)
        extra = timedelta(milliseconds=1)
        if any([s.dirty for s in self.strips]):
            return period + extra + self.last_push - datetime.now()
        return timedelta(seconds=1) + self.last_push - datetime.now()

    @coroutine
    def scheduler(self):
        """Scheduler for strip data pushes."""
        try:
            logging.info("starting scheduler")
            while True:
                yield Task(self.loop.add_timeout, self.next_tick())
                if self.next_tick() <= timedelta(0):
                    self.do_push()
                else:
                    logging.warning("skipping push...")
        except Exception as e:
            logging.exception(e)

    def do_push(self):
        self.last_push = datetime.now()
        strip_data = [ s.serialize() for s in self.strips ]

        for idx, payload in zip(range(8), strip_data):
            self.seq += 1
            message = struct.pack("i", self.seq) + bytes(idx+1) + bytes(payload)
            bytes_sent = self.sock.sendto(message, self.pp_addr)
            break

