from __future__ import print_function

import logging
import time

from math import sin, pi
from tornado import ioloop

from derpherder import DerpHerder



class RainbowsDemo():
  """Horribly inefficent demo to pump pixelpushers with rotating colors."""

  @staticmethod
  def oscillator(freq, phaseStart, t):
    return sin(2*pi*freq*t + phaseStart);

  @staticmethod
  def rgb_osc(freq=0.5, off=0, scale=lambda x: x):
    while True:
      t = time.time()
      yield [scale(RainbowsDemo.oscillator(freq, phase+off, t)) for phase in (0,2*pi/3,4*pi/3)]

  def __init__(self, on_pixels=50, off_pixels=0, freq=0.2):
    scale_fx = lambda x: int(0x55 * (x+1) / 2)
    self.on_pixels = on_pixels
    self.off_pixels = off_pixels
    self.freq = freq
    #offset_fx = lambda idx:(idx * (2*pi/on_pixels))
    offset_fx = lambda idx:idx * (4*pi/on_pixels)
    self.oscs = [self.rgb_osc(off=offset_fx(idx), scale=scale_fx, freq=freq) for idx in xrange(on_pixels)]
    self.off_pixel_values = [0,0,0] * off_pixels

  def data_for_strip(self, idx):
    # ignore strip id right now.
    active = [ color_value for osc in self.oscs for color_value in osc.next()]
    return active + self.off_pixel_values


def main():
  import cProfile
  rainbow = RainbowsDemo()

  logging.basicConfig(level=logging.INFO)
  logging.info("Rainbows...")

  d = DerpHerder()

  def on_connect(device):
    logging.info("New device for rainbows!")
    rainbows = RainbowsDemo(on_pixels=100, off_pixels=140, freq=0.2)


  callback = lambda x: print("CALLBACK for device: %s" % x.packet.header.mac_str())
  callbackb = lambda x: x.start_updates_with_source(rainbow.data_for_strip)
  callback2 = lambda x: print("CALLBACK lost device: %s" % x.packet.header.mac_str())

  d.add_callbacks(found=callback, lost=callback2)
  d.add_callbacks(found=callbackb)

  cProfile.run("ioloop.IOLoop.instance().start()")
  
if __name__ == "__main__":
  main()
