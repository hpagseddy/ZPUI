from helpers import setup_logger

import requests
import html2text
import pyfiglet

menu_name = "Browser Test"  # App name as seen in main menu while using the system

from subprocess import call
from time import sleep

from ui import Menu, TextReader, Printer, MenuExitException, UniversalInput, Refresher, DialogBox, ellipsize

logger = setup_logger(__name__, "info")

def get_request(url):
    req_get = requests.get(url)
    cont = unicode(req_get.content, "utf-8")
    if len(cont) == 0:
        if req_get.status_code == 200:
            TextReader(html2text.html2text(cont), i, o).activate()
        elif req_get.status_code == 404:
            Printer ("Error 404, Not Found!", i, o)
        elif req_get.status_code == 500:
            Printer ("Error 500, Internal server error!", i, o)
        else:
            TextReader(html2text.html2text(cont), i, o).activate()
    else:
        TextReader(html2text.html2text(cont), i, o).activate()


def main():

    link = UniversalInput(i, o, message="URL:", name="URL input").activate()

    get_request(link)
    

def bookmark():
    link = "https://wiki.zerophone.org/index.php/Main_Page"
    
    get_request(link)

#Callback global for ZPUI. It gets called when application is activated in the main menu
callback = None

i = None #Input device
o = None #Output device

def init_app(input, output):
    global callback, i, o
    i = input;
    o = output  # Getting references to output and input device objects and saving them as globals
    main_menu_contents = [
    ["Type URL", main],
    ["Bookmark", bookmark],
    ["Exit", 'exit']]
    main_menu = Menu(main_menu_contents, i, o, "Browser Menu")
    callback = main_menu.activate

