#!/usr/bin/env python

from apps.zero_app import ZeroApp
from ui.scrollable_element import TextReader
import subprocess

class TextReaderExample(ZeroApp):
    def __init__(self, i, o):
        super(TextReaderExample, self).__init__(i, o)
        self.menu_name = "Links test app"
        self.text_reader = TextReader(stdout, i, o, self.menu_name)

    def on_start(self):
        self.text_reader.activate()

out = subprocess.Popen(['links', '-dump', 'www.google.com'],
stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)

stdout,stderr = out.communicate()
