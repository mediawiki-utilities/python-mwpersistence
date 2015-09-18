import bz2
import gzip
import os

from ..errors import FileTypeError

FILE_READERS = {
    'gz': lambda fn: gzip.open(fn, 'rt', encoding='utf-8', errors='replace'),
    'bz2': lambda fn: bz2.open(fn, 'rt', encoding='utf-8', errors='replace'),
    'json': open
}
"""
Maps extensions to the strategy for opening/decompressing a file
"""

FILE_WRITERS = {
    'gz': lambda fn: gzip.open(fn, 'wt', encoding='utf-8', errors='replace'),
    'bz2': lambda fn: bz2.open(fn, 'wt', encoding='utf-8', errors='replace'),
    'plaintext': lambda fn: open(fn, 'w'),
    'json': lambda fn: open(fn, 'w')
}
"""
Maps compression types to the strategy for opening/compressing a file
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
        return filename, None
    else:
        return ".".join(parts[:-1]), parts[-1]


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
        raise FileNotFoundError("No such file: {0}".format(path))

    _, extension = extract_extension(path)

    if extension not in FILE_READERS:
        raise FileTypeError("Extension {0} is not supported."
                            .format(repr(extension)))

    return path


def normalize_dir(path):
    if os.path.exists(path) and not os.path.isdir(path):
        raise NotADirectoryError("Not a directory: {0}".format(path))
    else:
        os.makedirs(path, exist_ok=True)

    return path


def reader(path_or_f):
    """
    Turns a path to a compressed file into a file-like object of (decompressed)
    data.

    :Parameters:
        path : `str`
            the path to the dump file to read
    """
    if hasattr(path_or_f, "read"):
        return path_or_f
    else:
        path = path_or_f

    path = normalize_path(path)
    _, extension = extract_extension(path)

    reader_func = FILE_READERS[extension]

    return reader_func(path)


def output_dir_path(old_path, output_dir, compression):
    filename, extension = extract_extension(old_path)
    new_filename = filename + "." + compression
    return os.path.join(output_dir, new_filename)


def writer(path):
    """
    Creates a compressed file writer from for a path with a specified
    compression type.
    """
    filename, extension = extract_extension(path)
    if extension in FILE_WRITERS:
        writer_func = FILE_WRITERS[extension]
        return writer_func(path)
    else:
        raise RuntimeError("Output compression {0} not supported.  Type {1}"
                           .format(extension, tuple(FILE_WRITERS.keys())))
