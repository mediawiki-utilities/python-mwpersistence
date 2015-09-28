"""
This module implements a set of utilities for generating diffs and content
persistence, statistics from the command-line.  When the mwpersistence python
package is installed, an `mwpersistence` utility should be available from the
command-line.  Run `mwpersistence -h` for more information:


mwpersistence diffs2persistence
+++++++++++++++++++++++++++++++
.. automodule:: mwpersistence.utilities.diffs2persistence
    :noindex:

mwpersistence persistence2stats
+++++++++++++++++++++++++++++++
.. automodule:: mwpersistence.utilities.persistence2stats
    :noindex:

mwpersistence dump2stats
++++++++++++++++++++++++
.. automodule:: mwpersistence.utilities.dump2stats
    :noindex:

mwpersistence revdocs2stats
+++++++++++++++++++++++++++
.. automodule:: mwpersistence.utilities.revdocs2stats
    :noindex:

"""
from .diffs2persistence import diffs2persistence, drop_diff
from .diffs2persistence import process_args as diffs2persistence_args
from .persistence2stats import persistence2stats, drop_tokens
from .persistence2stats import process_args as persistence2stats_args
from .dump2stats import dump2stats
from .revdocs2stats import revdocs2stats

__all__ = [diffs2persistence, drop_diff, diffs2persistence_args,
           persistence2stats, drop_tokens, persistence2stats_args,
           dump2stats,
           revdocs2stats]
