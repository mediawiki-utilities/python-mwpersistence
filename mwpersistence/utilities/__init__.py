"""
This module implements a set of utilities for generating diffs and content
persistence, statistics from the command-line.  When the mwpersistence python
package is installed, an `mwpersistence` utility should be available from the
command-line.  Run `mwpersistence -h` for more information:


mwpersistence diffs2persistence
+++++++++++++++++++++++++++++++
.. automodule:: mwpersistence.utilities.diffs2persistence

mwpersistence persistence2stats
+++++++++++++++++++++++++++++++
.. automodule:: mwpersistence.utilities.persistence2stats

mwpersistence dump2stats
++++++++++++++++++++++++
.. automodule:: mwpersistence.utilities.dump2stats

"""
from .diffs2persistence import diffs2persistence, drop_diff
from .dump2stats import dump2stats
from .persistence2stats import persistence2stats, drop_tokens

__all__ = [diffs2persistence, dump2stats, persistence2stats]
