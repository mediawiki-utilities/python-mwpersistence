import os
import subprocess

file_open = open


def open(path):
    """
    Opens a snappy-compressed file as a decompressed file

    :Parameters:
        path : `str`
            the path to the dump file to read
    """
    p = subprocess.Popen(
        ['snzip', '-d', '-c', path],
        stdout=subprocess.PIPE
    )
    return p.stdout
