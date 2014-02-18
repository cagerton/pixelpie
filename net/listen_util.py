#!/usr/bin/env python3

"""
Listen for PixelPusher devices on the network

Usage:
    listen_util.py
"""
import socket
import logging

from device.discovery import DiscoveryPacket
from net.udp_listner import UDPListener
from device.pusher import Pusher
from lib.events import EventBus, Listener, Event, EventsMixin, EventHandlerFunction
from lib.mixin_utils import MixedClassMeta


BROADCAST_HOST = ''
BROADCAST_PORT = 7331
PP_LISTEN_PORT = 9897
BROADCAST_ADDR = (BROADCAST_HOST, BROADCAST_PORT)


class DiscoveryListener(UDPListener):
    """Listens for and discovery packets.instance
        Mix it in and override handle_discovery_packet...
    """

    def __init__(self, *args, **kwargs):
        logging.debug("%s.__init__ (DiscoveryListener)", self.__class__)
        self.spare_buffer = DiscoveryPacket()
        super(DiscoveryListener, self).__init__(*args, **kwargs)

    def open_socket(self) -> socket:
        """Overrides UDPListener"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((BROADCAST_HOST, BROADCAST_PORT))
        logging.info("Opened socket.")
        return sock

    def handle_datagram(self, fd):
        """Reads packet from the socket & hands it to handle_discovery_packet method."""
        packet_buffer = self.spare_buffer
        self.socket.recv_into(packet_buffer, packet_buffer.size())
        self.handle_discovery_packet(packet_buffer)

    def handle_error(self, fd):
        logging.error("IO Error. Closing socket.")
        self.close()

    def handle_discovery_packet(self, packet):
        """Override me!"""
        logging.error("Got packet. (Override me!)")


class PusherIndex(EventsMixin, DiscoveryListener, metaclass=MixedClassMeta):
    """Keeps track of all the pushers"""

    def __init__(self, *args, **kwargs):
        logging.debug("%s.__init__ (PusherIndex)", self.__class__)
        self.pushers = {}
        self.listeners = set()

    def handle_discovery_packet(self, packet:DiscoveryPacket):
        mac = packet.header.mac_str()
        if not mac in self.pushers:
            if not packet.p.pixelpusher.sane():
                logging.error("Bad packet?")
                return
            self.pushers[mac] = Pusher()
            logging.info("new pusher! %s at %s", mac, packet.header.ip_str())
        self.spare_buffer = self.pushers[mac].update_discovery(packet)
        self.signal('pp.update', obj=self.pushers[mac])

    def get_pushers(self) -> dict:
        """Returns all the pushers"""
        return self.pushers


