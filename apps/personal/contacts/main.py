# coding=utf-8
import argparse
import os

from apps import ZeroApp
from helpers import setup_logger
from ui import (NumberedMenu, Listbox, Menu, LoadingIndicator, DialogBox,
                PrettyPrinter as Printer,  UniversalInput)
from distutils.spawn import find_executable

from libs.address_book import AddressBook, Contact
from libs.webdav import vdirsyncer

logger = setup_logger(__name__, 'info')

class ContactApp(ZeroApp):
    def __init__(self, i, o):
        super(ContactApp, self).__init__(i, o)
        self.menu_name = 'Contacts'
        self.address_book = AddressBook()
        self.menu = None

    def on_start(self):
        self.reload()

    def reload(self):
        self.menu = NumberedMenu(self.build_main_menu_content(), self.i,
                                 self.o, prepend_numbers=False)
        self.menu.activate()

    def build_main_menu_content(self):
        all_contacts = self.address_book.contacts
        menu_entries = [['|| Actions', lambda: self.open_actions_menu()]]
        for c in all_contacts:
            menu_entries.append([c.short_name(), lambda x=c:
                                 self.open_contact_details_page(x)])

        return menu_entries

    def open_contact_details_page(self, contact):
        # type: (Contact) -> None
        contact_attrs = [getattr(contact, a) for a in
                         contact.get_filled_attributes()]
        Listbox(contact_attrs, self.i, self.o).activate()

    def open_actions_menu(self):
        menu_contents = [
            ['CardDAV Setup Wizard', lambda: self.open_remote_setup_wizard()],
            ['CardDAV Sync', lambda: self.synchronize_carddav()],
            ['Reset address book', lambda: self.reset_addressbook()]
        ]
        Menu(menu_contents, self.i, self.o, name='My menu').activate()

    def reset_addressbook(self):
        alert = 'This action will delete all of your contacts. Are you sure?'
        do_reset = DialogBox('yc', self.i, self.o, message=alert,
                             name='Address book reset').activate()

        if do_reset:
            self.address_book.reset()
            announce = 'All of your contacts were deleted.'
            Printer(announce, self.i, self.o, sleep_time=2, skippable=True)
            # Reload the now empty address book
            self.reload()

    def synchronize_carddav(self):
        with LoadingIndicator(self.i, self.o, message='Syncing contacts'):
            exit_status = vdirsyncer.sync('contacts')

        if (exit_status != 0):
            error_msg = "Error in contact synchronization. See ZPUI logs for \
            details."
            Printer(error_msg, self.i, self.o, sleep_time=3)
            self.open_actions_menu()

        with LoadingIndicator(self.i, self.o, message='Importing contacts'):
            self.address_book.import_vcards_from_directory(
                vdirsyncer.get_storage_directory_for('contacts')
            )

        # Reload the synced address book
        self.reload()

    def open_remote_setup_wizard(self):
        # Define wizard fields
        url_field = UniversalInput(self.i, self.o,
                                   message='CardDAV URL:',
                                   name='CardDAV URL field')
        username_field = UniversalInput(self.i, self.o,
                                        message='CardDAV Username:',
                                        name='CardDAV username field')
        password_field = UniversalInput(self.i, self.o,
                                        message='CardDAV Password:',
                                        name='CardDAV password field')

        # Run wizard
        url = url_field.activate()
        if not url: # If entry cancelled, exit the wizard
            return
        username = username_field.activate()
        if not username:
            return
        password = password_field.activate()
        if not password:
            return

        # Update ZPUI vdirsyncer config, generate vdirsyncer config file
        vdirsyncer.set_carddav_remote(url, username, password)
        vdirsyncer.generate_config()

        # Initialize vdirsyncer remote
        with LoadingIndicator(self.i, self.o, message='Initializing remote'):
            exit_status = vdirsyncer.discover('contacts')

        if (exit_status != 0):
            error_msg = "Error in remote initialization. Check vdirsyncer \
            configuration"
            Printer(error_msg, self.i, self.o, sleep_time=3)
            return

        # Synchronize contacts if the user request it
        sync_now = DialogBox('yn', self.i, self.o,
                             message='Remote saved. Sync now?',
                             name='Sync synced contacts').activate()
        if sync_now: self.synchronize_carddav()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    logger.info('Generating vdirsyncer configuration')
    parser.add_argument('-i', '--src-folder', dest='src_folder', action='store', metavar='DIR',
                        help='Folder to read vcard from', default=ZPUI_HOME)
    parser.add_argument('-t', '--run-tests', dest='test', action='store_true', default=False)
    arguments = parser.parse_args()

    if arguments.test:
        logger.info('Running tests...')
        doctest.testmod()

    address_book = AddressBook()
    address_book.import_vcards_from_directory(arguments.src_folder)
    address_book.save_to_file()
