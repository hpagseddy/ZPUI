from datetime import datetime
from time import sleep
from copy import copy

from ui import MockOutput, Canvas ,Zone, ZoneSpacer as ZS, \
                 VerticalZoneSpacer as VZS, ZoneManager

from ui.canvas import crop

from helpers import setup_logger

logger = setup_logger(__name__, "info")

icon_canvas = Canvas(MockOutput(22, 8))
hh_mm_canvas = Canvas(MockOutput(80, 30))
ss_canvas = Canvas(MockOutput(20, 10))
button_canvas = Canvas(MockOutput(40, 8))

counter = 0

from zerophone import api as zp_api

sources = ["wifi_connected", "wifi_strength", "dcdc_state", "charger_connected"]
values = {}

def check_sources_polling():
    if not zp_api.check_polled_sources(sources):
        zp_api.request_source_poll(sources)
    while not zp_api.check_polled_sources(sources):
        sleep(0.01)

def update_sources():
    global values
    values = zp_api.get_sources(sources)

def get_battery():
    return (0, values["charger_connected"] == True)

def draw_battery(value):
    level, charger_state = value
    icon_canvas.clear()
    icon_canvas.rectangle((2, 0, 20, 7))
    icon_canvas.rectangle((6, 0, 20, 7), fill="white")
    icon_canvas.rectangle((0, 1, 2, 6), fill="white")
    if charger_state:
        icon_canvas.text("Ch", (7, -1), fill="black")
    return copy(icon_canvas.get_image())

def get_gsm():
    return 55

def draw_gsm(value):
    icon_canvas.clear()
    icon_canvas.line((3, 1, 3, 6))
    icon_canvas.line((1, 1, 5, 1))
    icon_canvas.point(((1, 2), (5, 2)))
    offset = 7
    for x in reversed(range(6)):
        icon_canvas.line((x*2+offset, 6-x, x*2+offset, 6))
    return copy(icon_canvas.get_image())

def get_display():
    return counter % 2 == 0

def draw_display(value):
    icon_canvas.clear()
    if value:
        icon_canvas.rectangle((0, 0, 7, 5),)
        icon_canvas.line((3, 6, 4, 6))
        icon_canvas.line((1, 7, 6, 7))
    image = crop(icon_canvas.get_image(), min_height=8, align="top")
    return image

def get_usb():
    return values["dcdc_state"] == True

def draw_usb(value):
    icon_canvas.clear()
    if value:
        icon_canvas.text("U", (0, -1))
    image = crop(icon_canvas.get_image(), min_height=8, min_width=8, align="bottom")
    return image

def get_wifi():
    return (values["wifi_connected"], values["wifi_strength"])

def draw_wifi(value):
    is_on, strength = value
    icon_canvas.clear()
    if is_on:
        icon_canvas.text('W', (0, -1))
        offset = 7
        strength_mapping = [-90, -80, -70, -65, -60, -50, -30]
        level = 0
        if strength is not None and strength > -80:
            for i, element in enumerate(strength_mapping):
                if strength >= element and strength < strength_mapping[i+1] if i+1 < len(strength_mapping) else 0:
                    level = i
                    break
        icon_canvas.line((offset, str(-level), offset, 7))
    # top
    #icon_canvas.point( ((0, 1), (6, 1)), )
    #icon_canvas.line((1, 0, 5, 0), )
    # middle
    #icon_canvas.point( ((1, 3), (5, 3)), )
    #icon_canvas.line((2, 2, 4, 2), )
    # bottom
    #icon_canvas.point( ((0, 1), (6, 1)), )
    #icon_canvas.line((1, 0, 5, 0), )
    image = crop(icon_canvas.get_image(), min_height=8, min_width=10, align="bottom")
    return image

def get_hh_mm():
    return datetime.now().strftime("%H:%M")

def get_ss():
    return datetime.now().strftime("%S")

def draw_hh_mm(value):
    hh_mm_canvas.clear()
    hh_mm_canvas.text(value, (0, 0), font=("Fixedsys62.ttf", 32))
    return hh_mm_canvas.get_image()

def draw_ss(value):
    ss_canvas.clear()
    ss_canvas.text(value, (0, 0))
    return ss_canvas.get_image()

def draw_button(text):
    button_canvas.clear()
    button_canvas.centered_text(text)
    return copy(button_canvas.get_image())

zones = {"hh_mm":Zone(get_hh_mm, draw_hh_mm, name="HH_MM"),
         "ss":Zone(get_ss, draw_ss, name="SS"),
         "gsm":Zone(get_gsm, draw_gsm, name="gsm"),
         "wifi":Zone(get_wifi, draw_wifi, name="wifi"),
         "usb":Zone(get_usb, draw_usb, name="usb"),
         "display":Zone(get_display, draw_display, name="display"),
         "battery":Zone(get_battery, draw_battery, name="battery")}

markup = [
  [VZS(1)],
  [ZS(1), "gsm", ZS(1), "wifi", ZS(1), "usb", ZS(1), "display", "...", "battery"],
  [VZS(2)],
  ["hh_mm", ZS(3), "ss"],
]
