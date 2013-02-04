from pkg_resources import resource_filename #pylint: disable=E0611
from gi.repository import GLib #pylint: disable=E0611
from os.path import join
from os import path, makedirs

def data(filename):
    """Return path for storing data file with given name.

    Ensures the directory and file exists.
    """
    data_path = path.join(GLib.get_user_data_dir(), "netscramble")
    if not path.exists(data_path):
        makedirs(data_path)
    file_path = path.join(data_path, filename)
    if not path.exists(file_path):
        f = open(file_path, "w")
        f.close()
    return file_path

def res(filename):
    """Return absolute resource path for filename."""
    return resource_filename(__name__, filename)

