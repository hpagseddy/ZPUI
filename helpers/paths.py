"""Paths helpers

This module is used across ZPUI to obtain consistant path for configurations,
data and cache files.
"""

# Parts of this file are inspired from Scott Stevenson's xdg python package,
# licensed under the ISC licenses.
# See https://github.com/srstevenson/xdg/blob/3.0.2/xdg.py ;

import os
import sys

def _getenv(variable, default):
    return os.environ.get(variable) or default

def _ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path, 0760)

    if not os.path.isdir(path):
        raise os.error('Expected a directory but found file instead.')

def _zp_dir(path):
    path = os.path.join(path, 'zp')
    _ensure_directory_exists(path)
    return path

XDG_CACHE_HOME = _getenv(
    "XDG_CACHE_HOME", os.path.expandvars(os.path.join("$HOME", ".cache"))
)
XDG_CONFIG_HOME = _getenv(
    "XDG_CONFIG_HOME", os.path.expandvars(os.path.join("$HOME", ".config"))
)
XDG_DATA_HOME = _getenv(
    "XDG_DATA_HOME",
    os.path.expandvars(os.path.join("$HOME", ".local", "share")),
)
ZP_CACHE_DIR = _zp_dir(XDG_CACHE_HOME)
ZP_CONFIG_DIR = _zp_dir(XDG_CONFIG_HOME)
ZP_DATA_DIR = _zp_dir(XDG_DATA_HOME)

def local_path_gen(_name_):
    """This function generates a ``local_path`` function you can use
    in your scripts to get an absolute path to a file in your app's
    directory. You need to pass ``__name__`` to ``local_path_gen``. Example usage:

    .. code-block:: python

        from helpers import local_path_gen
        local_path = local_path_gen(__name__)
        ...
        config_path = local_path("config.json")

    The resulting local_path function supports multiple arguments,
    passing all of them to ``os.path.join`` internally."""
    app_path = os.path.dirname(sys.modules[_name_].__file__)

    def local_path(*path):
        return os.path.join(app_path, *path)
    return local_path
