# coding=utf-8
import argparse
import doctest

import os

from address_book import AddressBook, ZPUI_HOME
from contact import Contact
from apps import ZeroApp
from helpers import setup_logger
from ui import NumberedMenu, Listbox, Menu, LoadingIndicator, Printer
from distutils.spawn import find_executable

logger = setup_logger(__name__, "info")

VDIRSYNCER_CONFIG = '/tmp/vdirsyncer_config'
VDIRSYNCER_VCF_DIRECOTRY = '/tmp/contacts/contacts'

class ContactApp(ZeroApp):
    def __init__(self, i, o):
        super(ContactApp, self).__init__(i, o)
        self.menu_name = "Contacts"
        self.address_book = AddressBook()
        self.menu = None
        self.vdirsyncer_executable = find_executable('vdirsyncer')

    def on_start(self):
        self.address_book.load_from_file()
        self.menu = NumberedMenu(self.build_main_menu_content(), i=self.i,
                                 o=self.o, prepend_numbers=False)
        self.menu.activate()

    def build_main_menu_content(self):
        all_contacts = self.address_book.contacts
        menu_entries = []
        menu_entries.append(["|| Actions", lambda: self.open_actions_menu()])
        for c in all_contacts:
            menu_entries.append([c.short_name(), lambda x=c:
                                 self.open_contact_details_page(x)])

        return menu_entries

    def open_contact_details_page(self, contact):
        # type: (Contact) -> None
        contact_attrs = [getattr(contact, a) for a in
                         contact.get_filled_attributes()]
        Listbox(i=self.i, o=self.o, contents=contact_attrs).activate()

    def open_actions_menu(self):
        menu_contents = [
            ["Configure", lambda: self.open_settings_page()],
            ["Synchronize", lambda: self.synchronize_carddav(lambda: self.open_actions_menu())]
        ]
        Menu(menu_contents, i=self.i, o=self.o, name="My menu").activate()

    def open_settings_page(self):
        if self.vdirsyncer_executable:
            vdirsyncer_executable = self.vdirsyncer_executable
        else:
            vdirsyncer_executable = 'Not found'

        attrs = [
            ["-- VdirSyncer"],
            ["Executable: {}".format(vdirsyncer_executable) ],
            ["Config: {}".format(VDIRSYNCER_CONFIG)]
        ]
        Listbox(i=self.i, o=self.o, contents=attrs).activate()

    def synchronize_carddav(self, callback):
        if (not os.path.isfile(self.vdirsyncer_executable) or
        not os.access(self.vdirsyncer_executable, os.X_OK)):
            Printer('Could not execute vdirsyncer.', i=self.i, o=self.o,
                    sleep_time=2, skippable=True)
            callback()
            return;

        vdirsyncer_command = "{} -c {} sync contacts".format(
            self.vdirsyncer_executable, VDIRSYNCER_CONFIG
        )
        logger.info("Calling vdirsyncer to synchronize contacts")
        with LoadingIndicator(self.i, self.o, message="Syncing contacts"):
            exit_status = os.system(vdirsyncer_command)

        if (exit_status != 0):
            error_msg = 'Error in contact synchronization. Did you configure \
            vdirsyncer?'
            Printer(error_msg, i=self.i, o=self.o, sleep_time=2,
                    skippable=True)

        with LoadingIndicator(self.i, self.o, message="Importing contacts"):
            self.address_book.import_vcards_from_directory(VDIRSYNCER_VCF_DIRECOTRY)
            self.address_book.save_to_file()

        callback()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--src-folder', dest='src_folder', action='store', metavar="DIR",
                        help='Folder to read vcard from', default=ZPUI_HOME)
    parser.add_argument('-t', '--run-tests', dest='test', action='store_true', default=False)
    arguments = parser.parse_args()

    if arguments.test:
        logger.info("Running tests...")
        doctest.testmod()

    address_book = AddressBook()
    address_book.import_vcards_from_directory(arguments.src_folder)
    address_book.save_to_file()
