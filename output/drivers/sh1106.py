#!/usr/bin/python
from types import MethodType

from luma_driver import LumaScreen
from luma.oled.device import sh1106

from output.output import OutputDevice

from bitarray import bitarray
from array import array

#Monkey-patching SH1106 display function to allow for faster buffer conversions
def fast_display(self, image):
    assert(image.mode == self.mode)
    assert(image.size == self.size)

    image = self.preprocess(image)

    set_page_address = 0xB0
    image_data = image.getdata()
    pixels_per_page = self.width * 8
    buf = bitarray(pixels_per_page)
    buf.setall(0)

    image_bitarray = bitarray(image_data)
    #imgdata = (chr(i) for i in image_data)
    #image_bitarray.extend(imgdata)

    #for y in range(0, int(self._pages * pixels_per_page), pixels_per_page):
    for y in range(8):
        self.command(set_page_address, 0x02, 0x10)
        set_page_address += 1
        start = y*pixels_per_page
        for i in range(pixels_per_page):
            r = i >> 3
            c = i - (r << 3)
            buf[c*8 + r] = image_bitarray[start+i]
        #offsets = [y + self.width * i for i in range(8)]

        #for x in range(self.width):
        #    buf[x] = \
        #        (image_data[x + offsets[0]] and 0x01) | \
        #        (image_data[x + offsets[1]] and 0x02) | \
        #        (image_data[x + offsets[2]] and 0x04) | \
        #        (image_data[x + offsets[3]] and 0x08) | \
        #        (image_data[x + offsets[4]] and 0x10) | \
        #        (image_data[x + offsets[5]] and 0x20) | \
        #        (image_data[x + offsets[6]] and 0x40) | \
        #        (image_data[x + offsets[7]] and 0x80)
        intarray = array('b', buf.tobytes())
        self.data(list(intarray))


class Screen(LumaScreen, OutputDevice):
    """
    An object that provides high-level functions for interaction with display.
    It contains all the high-level logic and exposes an interface for system
    and applications to use.
    """

    def init_display(self, autoscroll=False, **kwargs):
        """Initializes SH1106 controller. """
        self.device = sh1106(self.serial, width=128, height=64)
        #self.device.display = MethodType(fast_display, self.device)
