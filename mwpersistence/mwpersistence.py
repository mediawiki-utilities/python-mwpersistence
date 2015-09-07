"""
This script provides access to a set of utilities for extracting content
persistence-based measurements from MediaWiki XML dumps.

* dump2diffs -- (1) Converts XML dumps to diff information (XML --> JSON)
* diffs2persistence -- (2) Converts diff information to token persistence
                           information (JSON --> JSON)
* persistence2stats -- (3) Converts token persistence information to
                           revision-level stats (JSON --> JSON)
* dump2stats -- (1,2,3) Full pipeline. From XML dumps to revision-level
                        stats (XML --> JSON)

Usage:
    mwpersistence -h | --help
    mwpersistence <utility> [-h | --help]

Options:
    -h | --help  Prints this documentation
    <utility>    The name of the utility to run
"""
import sys
import traceback
from importlib import import_module


USAGE = """Usage:
    mwpersistence -h | --help
    mwpersistence <utility> [-h | --help]\n"""


def main():

    if len(sys.argv) < 2:
        sys.stderr.write(USAGE)
        sys.exit(1)
    elif sys.argv[1] in ("-h", "--help"):
        sys.stderr.write(__doc__ + "\n")
        sys.exit(1)
    elif sys.argv[1][:1] == "-":
        sys.stderr.write(USAGE)
        sys.exit(1)

    module_name = sys.argv[1]
    try:
        module = import_module(".utilities." + module_name,
                               package="mwpersistence")
    except ImportError:
        sys.stderr.write(traceback.format_exc())
        sys.stderr.write("Could not load utility {0}.\n".format(module_name))
        sys.exit(1)

    module.main(sys.argv[2:])
