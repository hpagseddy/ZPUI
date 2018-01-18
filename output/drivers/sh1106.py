#!/usr/bin/python
from types import MethodType

from luma_driver import LumaScreen
from luma.oled.device import sh1106

from output.output import OutputDevice

#Monkey-patching SH1106 display function to allow for quasi-"diff-to-previous" redraws
def partial_display(self, image):
    assert(image.mode == self.mode)
    assert(image.size == self.size)

    #image = self.preprocess(image)

    set_page_address = 0xB0
    image_data = image.getdata()
    pixels_per_page = self.width * 8
    buf = bytearray(self.width)

    for y in range(0, int(self._pages * pixels_per_page), pixels_per_page):
        previous_buf = self.previous_buffers[y/pixels_per_page]
        self.command(set_page_address, 0x02, 0x10)
        set_page_address += 1
        offsets = [y + self.width * i for i in range(8)]

        for x in range(self.width):
            buf[x] = \
                (image_data[x + offsets[0]] and 0x01) | \
                (image_data[x + offsets[1]] and 0x02) | \
                (image_data[x + offsets[2]] and 0x04) | \
                (image_data[x + offsets[3]] and 0x08) | \
                (image_data[x + offsets[4]] and 0x10) | \
                (image_data[x + offsets[5]] and 0x20) | \
                (image_data[x + offsets[6]] and 0x40) | \
                (image_data[x + offsets[7]] and 0x80)
        if buf != previous_buf:
             self.data(list(buf))
        self.previous_buffers[y/pixels_per_page] = buf




class Screen(LumaScreen, OutputDevice):
    """
    An object that provides high-level functions for interaction with display.
    It contains all the high-level logic and exposes an interface for system
    and applications to use.
    """

    def init_display(self, autoscroll=False, **kwargs):
        """Initializes SH1106 controller. """
        self.device = sh1106(self.serial, width=128, height=64)
        self.device.previous_buffers = [bytearray(self.device.width) for i in range(self.device._pages)]
        self.device.display = MethodType(partial_display, self.device)
