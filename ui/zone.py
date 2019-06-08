from copy import copy

from canvas import Canvas
from base_ui import BaseUIElement

from helpers import setup_logger

logger = setup_logger(__name__, "info")

"""
Zone requirements:
- get values from a callback
- get new zone images from an image-generating callback, passing value to the callback
- only get a new image when the value changes
- cache the images for the values
"""

class Zone(object):
    """
    Allows us to avoid re-generating icons/graphics for different values,
    i.e. if we need to draw a clock, we can use zones to avoid redrawing
    the hours/minutes too often and save some CPU time. Also implements
    caching, so after some time we won't need to redraw, say, seconds -
    just getting the cached image for each of the 60 possible values.
    """
    value = None
    image = None
    prev_value = None

    def __init__(self, value_cb, image_cb, caching = True, i_pass_self = False, v_pass_self = False, name=None):
        self.value_cb = value_cb
        self.image_cb = image_cb
        self.caching = caching
        self.v_pass_self = v_pass_self
        self.i_pass_self = i_pass_self
        self.name = name
        if self.caching:
            self.cache = {}

    def needs_refresh(self):
        # Getting new value
        if self.v_pass_self:
            new_value = self.value_cb(self)
        else:
            new_value = self.value_cb()
        if new_value != self.value:
            logger.debug("Zone {}: new value {}".format(self.name, new_value))
            # New value!
            self.prev_value = self.value
            self.value = new_value
            return True
        return False

    def update_image(self):
        # Checking the cache
        if self.caching:
            if self.value in self.cache:
                return self.cache[self.value]
        # Not caching or not found - generating
        if self.i_pass_self:
            image = self.image_cb(self.value, self)
        else:
            image = self.image_cb(self.value)
        # If caching, storing
        if self.caching:
            self.cache[self.value] = copy(image)
        return image

    def get_image(self):
        return self.image

    def refresh(self):
        if self.needs_refresh():
            self.image = self.update_image()
            return True
        return False

class ZoneSpacer(object):
    def __init__(self, value):
        self.value = value

class VerticalZoneSpacer(ZoneSpacer):
    pass

class ZoneManager(object):

    def __init__(self, i, o, markup, zones, name="ZoneManager", **kwargs):
        self.zones = zones
        self.markup = markup
        self.zones_that_need_refresh = {}
        self.row_heights = []
        self.item_widths = []
        self.refresh_on_start()
        self.name = name
        self.c = Canvas(o)
        self.o = o
        self.i = i

    def refresh_on_start(self):
        for name, zone in self.zones.items():
            zone.refresh()
            self.zones_that_need_refresh[name] = True
        for row in self.markup:
            self.item_widths.append([])
            self.row_heights.append(0)

    def get_element_height(self, element):
        if element in self.zones:
            return self.zones[element].get_image().height
        elif isinstance(element, VerticalZoneSpacer):
            return element.value

    def get_element_width(self, element):
        if element in self.zones:
            return self.zones[element].get_image().width
        elif isinstance(element, ZoneSpacer) \
         and not isinstance(element, VerticalZoneSpacer):
            return element.value

    def update(self):
        full_redraw = False
        row_heights = []
        for i, row in enumerate(self.markup):
            for item in row:
                if item in self.zones:
                    zone = self.zones[item]
                    has_refreshed = zone.refresh()
                    if has_refreshed and not self.zones_that_need_refresh[item]:
                        self.zones_that_need_refresh[item] = True
                else:
                    if isinstance(item, basestring):
                        if not all([char == "." for char in item]):
                            logger.warning("Zone {} unknown!".format(item))
                    elif isinstance(item, (ZoneSpacer, VerticalZoneSpacer)):
                        pass
            item_heights = [self.get_element_height(item) for item in row]
            if filter(None, item_heights):
                row_height = max(item_heights)
            else:
                row_height = None
            row_heights.append(row_height)
        if row_heights != self.row_heights:
            # Row heights changed!
            # print("Row heights changed!")
            self.row_heights = row_heights
            full_redraw = True
        # Calculating vertical spacing between rows
        empty_row_amount = row_heights.count(None)
        if empty_row_amount == 0:
            pass # will just leave empty space at the bottom
        else: # One or more empty rows
            # Let's redistribute the empty space equally
            empty_space = self.o.height-sum(filter(None, row_heights))
            # Unless there's no space to redistribute, that is
            if empty_space > 0:
                for i, el in enumerate(row_heights):
                    spacing = int(empty_space/empty_row_amount)
                    if el is None:
                        row_heights[i] = spacing
        #print(self.item_widths)
        for i, row in enumerate(self.markup):
            item_widths = [self.get_element_width(item) for item in row]
            if item_widths != self.item_widths[i]:
                # Item widths changed!
                #print("Item widths changed! Row {}, {} => {}".format(i, self.item_widths[i], item_widths))
                self.item_widths[i] = item_widths
                full_redraw = True
        #print(self.item_widths)
        if full_redraw:
            self.c.clear()
        # Redrawing the elements (only those we need to redraw)
        y = 0
        for i, row in enumerate(self.markup):
            x = 0
            row_height = row_heights[i]
            item_widths = copy(self.item_widths[i])
            # Calculating horizontal spacing between items
            empty_item_amount = item_widths.count(None)
            if empty_item_amount == 0:
                pass # will just leave empty space on the right
            else: # One or more empty items
                # Let's redistribute the empty space equally
                empty_space = self.o.width-sum(filter(None, item_widths))
                # Unless there's no space to redistribute, that is
                if empty_space > 0:
                    spacing = int(empty_space/empty_item_amount)
                    for i, el in enumerate(item_widths):
                        if el is None:
                            item_widths[i] = spacing
            for i, item in enumerate(row):
                width = item_widths[i]
                if item not in self.zones:
                    x += width
                    continue
                image = self.zones[item].get_image()
                if self.zones_that_need_refresh[item] or full_redraw:
                    self.c.clear((x, y, x+image.width, y+row_height))
                    self.c.paste(image, (x, y))
                    self.zones_that_need_refresh[item] = False
                x += width
            y += row_height

    def get_image(self):
        return self.c.get_image()
