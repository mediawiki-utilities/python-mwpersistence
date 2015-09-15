import bz2
import gzip
import os

from . import snappy
from ..errors import FileTypeError

FILE_OPENERS = {
    'xml': open,
    'gz': gzip.open,
    'bz2': bz2.open,
    'json': open,
    'snappy': snappy.open
}
"""
Maps extensions to the strategy for opening/decompressing a file
"""


def extract_extension(path):
    """
    Reads a file path and returns the extension or None if the path
    contains no extension.

    :Parameters:
        path : str
            A filesystem path
    """
    filename = os.path.basename(path)
    parts = filename.split(".")
    if len(parts) == 1:
        return None
    else:
        return parts[-1]


def normalize_path(path_or_f):
    """
    Verifies that a file exists at a given path and that the file has a
    known extension type.

    :Parameters:
        path_or_f : `str` | `file`
            the path to a dump file or a file handle

    """
    if hasattr(path_or_f, "read"):
        return path_or_f
    else:
        path = path_or_f

    path = os.path.expanduser(path)

    # Check if exists and is a file
    if os.path.isdir(path):
        raise IsADirectoryError("Is a directory: {0}".format(path))
    elif not os.path.isfile(path):
        raise FileNotFoundError("No such file or directory: {0}".format(path))

    extension = extract_extension(path)

    if extension not in FILE_OPENERS:
        raise FileTypeError("Extension {0} is not supported."
                            .format(repr(extension)))

    return path


def open(path_or_f):
    """
    Turns a path to a dump file into a file-like object of (decompressed)
    XML data.

    :Parameters:
        path : `str`
            the path to the dump file to read
    """
    if hasattr(path_or_f, "read"):
        return path_or_f
    else:
        path = path_or_f

    path, extension = normalize_path(path), extract_extension(path)

    open_func = FILE_OPENERS[extension]

    return open_func(path)
