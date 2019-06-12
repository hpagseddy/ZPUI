import os
from datetime import datetime
from threading import Event

from mock import Mock
from apps import ZeroApp
from ui import Refresher, Canvas, FunctionOverlay

from PIL import ImageFont

import menu_markup

class App(ZeroApp):

    menu_name = "Main screen"

    def __init__(self, *args, **kwargs):
        ZeroApp.__init__(self, *args, **kwargs)
        self.zm = menu_markup.ZoneManager(self.i, self.o, menu_markup.markup,
                                     menu_markup.zones, refresh_on_start=False)
        self.fo = FunctionOverlay(["deactivate", "deactivate"], labels=["Exit", "Tools"], wrap_view=False)
        self.screen = MainScreen(self.get_image, self.i, self.o, name="Main screen", refresh_interval=1)
        self.fo.apply_to(self.screen)

    def get_image(self):
        self.zm.update()
        image = self.zm.get_image()
        image = self.fo.modify_image_if_needed(self.screen, image)
        return image

    def set_context(self, c):
        self.context = c

    def on_start(self, *args, **kwargs):
        menu_markup.check_sources_polling()
        menu_markup.update_sources()
        self.zm.refresh_on_start()
        self.screen.activate()

class MainScreen(Refresher):
    def before_foreground(self, *a, **k):
        menu_markup.check_sources_polling()
        Refresher.before_foreground(self, *a, **k)

    def refresh(self):
        if self.is_active:
            menu_markup.update_sources()
        Refresher.refresh(self)
