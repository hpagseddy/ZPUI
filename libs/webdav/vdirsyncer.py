""" Vdirsyncer interface
This modules provides a basic interface over vdirsyncer [0]:

> Vdirsyncer is a command-line tool for synchronizing calendars and addressbooks
> between a variety of servers and the local filesystem.

[0] https://vdirsyncer.pimutils.org/en/stable/
"""

from jinja2 import Template, Environment, FileSystemLoader
from helpers import ZP_CONFIG_DIR, ZP_DATA_DIR, write_config
from main import load_config
import os

from helpers.logger import setup_logger
logger = setup_logger(__name__, "info")

DEFAULT_VDIRSYNCER_BINARY = '/usr/bin/vdirsyncer'
DEFAULT_VDIRSYNCER_CONFIG_FILE = os.path.join(ZP_CONFIG_DIR,
                                              'vdirsyncer_config')
DEFAULT_VDIRSYNCER_STORAGE_DIRECTORY = os.path.join(ZP_DATA_DIR, 'vdirsyncer')

def _execute(vdirsyncer_args):
    zp_config = load_config()[0]
    zp_vdirsyncer_config = zp_config.get('vdirsyncer', {})
    vdirsyncer_binary = zp_vdirsyncer_config.get(
        'binary', DEFAULT_VDIRSYNCER_BINARY
    )
    vdirsyncer_config_file = zp_vdirsyncer_config.get(
        'config_file', DEFAULT_VDIRSYNCER_CONFIG_FILE
    )

    vdirsyncer_command = "{} -c {}".format(vdirsyncer_binary,
                                           vdirsyncer_config_file)
    vdirsyncer_command += ' ' + ' '.join(vdirsyncer_args)

    logger.info("External binary call: {}".format(vdirsyncer_command))
    return os.system(vdirsyncer_command)

def sync(vdirsyncer_pair):
    """ This function synchronize two vdirsyncer storage entries, given a pair.

    A pair, defined in vdirsyncer's configuration, is usually composed of a
    local directory and a remote (CardDAV, CalDAV, ...). Do not forget to
    initialize the mapping with discover/1 before the first synchronization.
    """
    return _execute(['sync', vdirsyncer_pair])

def discover(vdirsyncer_pair):
    """ This function scans and initialize the storage entries of a pair. It
    must be run before the initial synchronization, and after every change to
    vdirsyncer's configuration.

    **If the pair contains a local directory which does not exist, vdirsycner
    will ask on the standard input whether to create it or not: this will block
    ZPUI.**
    """
    return _execute(['discover', vdirsyncer_pair])

# TODO: add support for multiple remotes
def set_carddav_remote(url, username, password):
    """ This function configure the (unique) CardDAV remote in ZPUI's
    configuration. You will have to run generate_config/0 in order to write
    vdirsyncer's configuration to disk.
    """
    zp_config, zp_config_path = load_config()
    zp_vdirsyncer_config = zp_config.get('vdirsyncer', {})
    contacts_storage_directory = get_storage_directory_for('contacts')

    zp_vdirsyncer_config['contacts'] = {
        'pair': {
            'a': 'contacts_local',
            'b': 'contacts_remote',
            'collections': 'null'
        },
        'local': {
            'type': 'filesystem',
            'path': contacts_storage_directory,
            'fileext': '.vcf'
        },
        'remote': {
            'type': 'carddav',
            'url': url,
            'username': username,
            'password': password
        }
    }

    zp_config['vdirsyncer'] = zp_vdirsyncer_config
    return write_config(zp_config, zp_config_path)

def get_storage_directory_for(pair):
    """ Returns the path of the local storage for a given pair.

    A pair, defined in vdirsyncer's configuration, is usually composed of a
    local directory and a remote (CardDAV, CalDAV, ...). This function returns
    the path to the local directory containing vcf (for a CardDAV remote)
    or ics (for a CalDAV remote) files.
    """
    zp_config = load_config()[0]
    zp_vdirsyncer_config = zp_config.get('vdirsyncer', {})
    vdirsyncer_storage_directory = zp_vdirsyncer_config.get(
        'storage_directory', DEFAULT_VDIRSYNCER_STORAGE_DIRECTORY
    )

    directory = os.path.join(vdirsyncer_storage_directory, pair)

    # Create the directory ourself so that vdirsyncer does not ask stdin!
    if not os.path.exists(directory):
        os.makedirs(directory)

    return directory

# TODO: similar to set_carddav_remote
def set_calddav_remote():
    """ Not yet implemented.
    """
    return

def generate_config():
    """ Generate and write to disk vdirsyncer's configuration file, based on
    ZPUI's configuration. You must run discover/1 afterwards if the
    configuration was modified.
    """
    zp_config = load_config()[0]
    zp_vdirsyncer_config = zp_config.get('vdirsyncer', {})
    status_directory = get_storage_directory_for('_vdirsyncer_status')

    logger.info('Generating vdirsyncer configuration')

    jinja2_env = Environment(loader=FileSystemLoader('libs/webdav'),
                             trim_blocks=True)
    template = jinja2_env.get_template('vdirsyncer_config.j2')
    rendered_vdirsyncer_config = template.render(
        contacts=zp_vdirsyncer_config['contacts'],
        status_directory=status_directory
    )

    vdirsyncer_config_file = zp_vdirsyncer_config.get(
        'config_file', DEFAULT_VDIRSYNCER_CONFIG_FILE
    )

    logger.info('Writing vdirsyncer configuration')
    # FIXME: ensure file is not world-readable
    with open(vdirsyncer_config_file, 'w') as fh:
        fh.write(rendered_vdirsyncer_config)
