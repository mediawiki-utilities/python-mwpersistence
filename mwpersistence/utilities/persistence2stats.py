r"""
``$ mwpersistence persistence2stats -h``
::

    Aggregates a stream of token persistence stats into revision statistics.
    RevisionDocument JSON blobs are printed to <stdout> with an additional
    'stats' field.

    Note that the 'persistence' field will be deleted (to save space) unless
    the `--keep-persistence` flag is used.

    Usage:
        persistence2stats (-h | --help)
        persistence2stats [<persistence-file>...] [--min-persisted=<num>]
                          [--min-visible=<days>] [--include=<regex>]
                          [--exclude=<regex>] [--keep-tokens] [--threads=<num>]
                          [--output=<path>] [--compress=<type>] [--verbose]

    Options:
        -h|--help              Print this documentation
        <persistence-file>     The path to a file containing persistence data.
        --min-persisted=<num>  The minimum number of revisions a token must
                               survive before being considered "persisted"
                               [default: 5]
        --min-visible=<days>   The minimum amount of time a token must survive
                               before being considered "persisted" (in days)
                               [default: 14]
        --include=<regex>      A regex matching tokens to include (case
                               insensitive) [default: <all>]
        --exclude=<regex>      A regex matching tokens to exclude (case
                               insensitive) [default: <none>]
        --keep-tokens          Do not drop 'tokens' field data from the JSON
                               document.
        --threads=<num>        If a collection of files are provided, how many
                               processor threads should be prepare?
                               [default: <cpu_count>]
        --output=<path>        Write output to a directory with one output file
                               per input path.  [default: <stdout>]
        --compress=<type>      If set, output written to the output-dir will be
                               compressed in this format. [default: bz2]
        --verbose              Print out progress information
"""
import json
import logging
import re
import sys
from math import log
from multiprocessing import cpu_count

import docopt
import para

from .. import files
from .util import drop_tokens, normalize_doc

logger = logging.getLogger(__name__)


def main(argv=None):
    args = docopt.docopt(__doc__, argv=argv)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(name)s -- %(message)s'
    )

    if len(args['<persistence-file>']) == 0:
        paths = [sys.stdin]
    else:
        paths = [files.normalize_path(path)
                 for path in args['<persistence-file>']]

    min_persisted, min_visible, include, exclude, keep_tokens = \
        process_args(args)

    if args['--threads'] == "<cpu_count>":
        threads = cpu_count()
    else:
        threads = int(args['--threads'])

    if args['--output'] == "<stdout>":
        output_dir = None
        logger.info("Writing output to stdout.  Ignoring 'compress' setting.")
        compression = None
    else:
        output_dir = files.normalize_dir(args['--output'])
        compression = args['--compress']

    if args['--output'] == "<stdout>":
        output_dir = None
        logger.info("Writing output to stdout.  Ignoring 'compress' setting.")
        compression = None
    else:
        output_dir = files.normalize_dir(args['--output'])
        compression = args['--compress']

    verbose = bool(args['--verbose'])

    run(paths, min_persisted, min_visible, include, exclude, keep_tokens,
        threads, output_dir, compression, verbose)


def process_args(args):
    min_persisted = int(args['--min-persisted'])

    # Converts from days to seconds
    min_visible = float(args['--min-visible']) * (60 * 60 * 24)

    if args['--include'] == "<all>":
        include = None
    else:
        include_re = re.compile(args['--include'], re.UNICODE | re.I)
        include = lambda t: bool(include_re.search(t))

    if args['--exclude'] == "<none>":
        exclude = None
    else:
        exclude_re = re.compile(args['--exclude'], re.UNICODE | re.I)
        exclude = lambda t: bool(exclude_re.search(t))

    keep_tokens = bool(args['--keep-tokens'])

    return min_persisted, min_visible, include, exclude, keep_tokens


def run(paths, min_persisted, min_visible, include, exclude, keep_tokens,
        threads, output_dir, compression, verbose):

    def process_path(path):
        f = files.reader(path)
        rev_docs = persistence2stats((normalize_doc(json.loads(line))
                                      for line in f),
                                     min_persisted, min_visible, include,
                                     exclude, verbose=False)

        if not keep_tokens:
            rev_docs = drop_tokens(rev_docs)

        if output_dir == None:
            yield from rev_docs
        else:
            new_path = files.output_dir_path(path, output_dir, compression)
            writer = files.writer(new_path)
            for rev_doc in rev_docs:
                json.dump(rev_doc, writer)
                writer.write("\n")

    for rev_doc in para.map(process_path, paths, mappers=threads):
        json.dump(rev_doc, sys.stdout)
        sys.stdout.write("\n")


def persistence2stats(rev_docs, min_persisted=5, min_visible=1209600,
                      include=None, exclude=None, verbose=False):
    """
    Processes a sorted and page-partitioned sequence of revision documents into
    and adds statistics to the 'persistence' field each token "added" in the
    revision persisted through future revisions.

    :Parameters:
        rev_docs : `iterable` ( `dict` )
            JSON documents of revision data containing a 'diff' field as
            generated by ``dump2diffs``.  It's assumed that rev_docs are
            partitioned by page and otherwise in chronological order.
        window_size : `int`
            The size of the window of revisions from which persistence data
            will be generated.
        min_persisted : `int`
            The minimum future revisions that a token must persist in order
            to be considered "persistent".
        min_visible : `int`
            The minimum number of seconds that a token must be visible in order
            to be considered "persistent".
        include : `func`
            A function that returns `True` when a token should be included in
            statistical processing
        exclude : `str` | `re.SRE_Pattern`
            A function that returns `True` when a token should *not* be
            included in statistical processing (Takes precedence over
            'include')
        verbose : `bool`
            Prints out dots and stuff to stderr

    :Returns:
        A generator of rev_docs with a 'persistence' field containing
        statistics about individual tokens.
    """
    min_persisted = int(min_persisted)
    min_visible = int(min_visible)
    include = include if include is not None else lambda t: True
    exclude = exclude if exclude is not None else lambda t: False

    for rev_doc in rev_docs:
        persistence_doc = rev_doc['persistence']
        stats_doc = {
            'tokens_added': 0,
            'persistent_tokens': 0,
            'non_self_persistent_tokens': 0,
            'sum_log_persisted': 0,
            'sum_log_non_self_persisted': 0,
            'sum_log_seconds_visible': 0,
            'censored': False,
            'non_self_censored': False
        }

        filtered_docs = (t for t in persistence_doc['tokens']
                         if include(t['text']) and not exclude(t['text']))
        for token_doc in filtered_docs:
            if verbose:
                sys.stderr.write(".")

            stats_doc['tokens_added'] += 1
            stats_doc['sum_log_persisted'] += log(token_doc['persisted'] + 1)
            stats_doc['sum_log_non_self_persisted'] += \
                log(token_doc['non_self_persisted'] + 1)
            stats_doc['sum_log_seconds_visible'] += \
                log(token_doc['seconds_visible'] + 1)

            # Look for time threshold
            if token_doc['seconds_visible'] >= min_visible:
                stats_doc['persistent_tokens'] += 1
                stats_doc['non_self_persistent_tokens'] += 1
            else:
                # Look for review threshold
                stats_doc['persistent_tokens'] += \
                    token_doc['persisted'] >= min_persisted

                stats_doc['non_self_persistent_tokens'] += \
                    token_doc['non_self_persisted'] >= min_persisted

                # Check for censoring
                if persistence_doc['seconds_possible'] < min_visible:
                    stats_doc['censored'] = True
                    stats_doc['non_self_censored'] = True

                else:
                    if persistence_doc['revisions_processed'] < min_persisted:
                        stats_doc['censored'] = True

                    if persistence_doc['non_self_processed'] < min_persisted:
                        stats_doc['non_self_censored'] = True

        if verbose:
            sys.stderr.write("\n")

        rev_doc['persistence'].update(stats_doc)

        yield rev_doc
