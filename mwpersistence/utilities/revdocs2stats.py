r"""
``$ mwpersistence revdocs2stats -h``
::

    Full pipeline from JSON revision documents to content persistence
    statistics.

    Usage:
        revdocs2stats (-h|--help)
        revdocs2stats [<input-file>...] --config=<path> --sunset=<date>
                      [--namespaces=<ids>] [--timeout=<secs>]
                      [--window=<revs>] [--revert-radius=<revs>]
                      [--min-persisted=<num>] [--min-visible=<days>]
                      [--include=<regex>] [--exclude=<regex>]
                      [--keep-text] [--keep-diff] [--keep-tokens]
                      [--threads=<num>] [--output=<path>] [--compress=<type>]
                      [--verbose] [--debug]

    Options:
        -h|--help               Print this documentation
        <input-file>            The path to a file of page-partitioned JSON
                                revision documents. [default: <stdin>]
        --config=<path>         The path to a deltas DiffEngine configuration
        --namespaces=<ids>      A comma separated list of namespace IDs to be
                                considered [default: <all>]
        --timeout=<secs>        The maximum number of seconds that a diff will
                                be allowed to run before being stopped
                                [default: 10]
        --sunset=<date>         The date of the database dump we are generating
                                from.  This is used to apply a 'time visible'
                                statistic.  Expects %Y-%m-%dT%H:%M:%SZ".
                                [default: <now>]
        --window=<revs>         The size of the window of revisions from which
                                persistence data will be generated.
                                [default: 50]
        --revert-radius=<revs>  The number of revisions back that a revert can
                                reference. [default: 15]
        --min-persisted=<num>   The minimum number of revisions a token must
                                survive before being considered "persisted"
                                [default: 5]
        --min-visible=<days>    The minimum amount of time a token must survive
                                before being considered "persisted" (in days)
                                [default: 14]
        --include=<regex>       A regex matching tokens to include
                                [default: <all>]
        --exclude=<regex>       A regex matching tokens to exclude
                                [default: <none>]
        --keep-text             If set, the 'text' field will be populated in
                                the output JSON.
        --keep-diff             If set, the 'diff' field will be populated in
                                the output JSON.
        --keep-tokens           If set, the 'tokens' field will be populated in
                                the output JSON.
        --threads=<num>         If a collection of files are provided, how many
                                processor threads should be prepare?
                                [default: <cpu_count>]
        --output=<path>         Write output to a directory with one output
                                file per input path.  [default: <stdout>]
        --compress=<type>       If set, output written to the output-dir will
                                be compressed in this format. [default: bz2]
        --verbose               Print progress information to stderr.
        --debug                 Print debug logging to stderr.
"""
import logging

import mwcli
import mwxml.utilities

import mwdiffs.utilities

from .diffs2persistence import process_args as diffs2persistence_args
from .diffs2persistence import diffs2persistence, drop_diff
from .persistence2stats import process_args as persistence2stats_args
from .persistence2stats import drop_tokens, persistence2stats

logger = logging.getLogger(__name__)


def process_args(args):
    kwargs = mwdiffs.utilities.dump2diffs_args(args)
    kwargs.update(diffs2persistence_args(args))
    kwargs.update(persistence2stats_args(args))
    return kwargs


def revdocs2stats(rev_docs, diff_engine, namespaces, timeout, window_size,
                  revert_radius, sunset, min_persisted, min_visible,
                  include, exclude, keep_text=False, keep_diff=False,
                  keep_tokens=False, verbose=False):

    diff_docs = mwdiffs.utilities.revdocs2diffs(rev_docs, diff_engine,
                                                namespaces, timeout)
    if not keep_text:
        diff_docs = mwdiffs.utilities.drop_text(diff_docs)

    persistence_docs = diffs2persistence(
        diff_docs, window_size, revert_radius, sunset, verbose=verbose)
    if not keep_diff:
        persistence_docs = drop_diff(persistence_docs)

    stats_docs = persistence2stats(
        persistence_docs, min_persisted, min_visible, include, exclude)
    if not keep_tokens:
        stats_docs = drop_tokens(stats_docs)

    yield from stats_docs


streamer = mwcli.Streamer(
    __doc__,
    __name__,
    revdocs2stats,
    process_args
)
main = streamer.main
