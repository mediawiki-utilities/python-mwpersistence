r"""
``$ mwpersistence diffs2persistence -h``
::

    Full pipeline from MediaWiki XML dumps to content persistence statistics.

    Usage:
        dump2stats (-h|--help)
        dump2stats [<dump_file>...] --config=<path> --sunset=<date>
                   [--namespaces=<ids>] [--timeout=<secs>]
                   [--window=<revs>] [--revert-radius=<revs>]
                   [--min-persisted=<num>] [--min-visible=<days>]
                   [--include=<regex>] [--exclude=<regex>]
                   [--keep-text] [--keep-diff] [--keep-tokens]
                   [--threads=<num>] [--output=<path>] [--compress=<type>]
                   [--verbose]

    Options:
        -h|--help               Print this documentation
        <dump-file>             The path to a MediaWiki XML Dump file
                                [default: <stdin>]
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
"""
import json
import logging
import sys
from multiprocessing import cpu_count

import docopt
import mwxml

from . import diffs2persistence, dump2diffs, persistence2stats
from .. import files
from .util import drop_diff, drop_text, drop_tokens

logger = logging.getLogger(__name__)


def main(argv=None):
    args = docopt.docopt(__doc__, argv=argv)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(name)s -- %(message)s'
    )

    if len(args['<dump_file>']) == 0:
        paths = [sys.stdin]
    else:
        paths = args['<dump_file>']

    diff_engine, namespaces, timeout, keep_text = dump2diffs.process_args(args)
    window_size, revert_radius, sunset, keep_diff = \
        diffs2persistence.process_args(args)
    min_persisted, min_visible, include, exclude, keep_tokens = \
        persistence2stats.process_args(args)

    if args['--threads'] == "<cpu_count>":
        threads = cpu_count()
    else:
        threads = int(args['--threads'])

    verbose = bool(args['--verbose'])

    if args['--output'] == "<stdout>":
        output_dir = None
        logger.info("Writing output to stdout.  Ignoring 'compress' setting.")
        compression = None
    else:
        output_dir = files.normalize_dir(args['--output'])
        compression = args['--compress']

    run(paths, diff_engine, namespaces, timeout, window_size, revert_radius,
        sunset, min_persisted, min_visible, include, exclude, keep_text,
        keep_diff, keep_tokens, threads, output_dir, compression, verbose)


def run(paths, diff_engine, namespaces, timeout, window_size, revert_radius,
        sunset, min_persisted, min_visible, include, exclude, keep_text,
        keep_diff, keep_tokens, threads, output_dir, compression, verbose):

    def process(dump, path):
        diff_docs = dump2diffs.dump2diffs(dump, diff_engine, namespaces,
                                          timeout)
        if not keep_text:
            diff_docs = drop_text(diff_docs)

        persistence_docs = diffs2persistence.diffs2persistence(
            diff_docs, window_size, revert_radius, sunset, verbose=verbose)
        if not keep_diff:
            persistence_docs = drop_diff(persistence_docs)

        stats_docs = persistence2stats.persistence2stats(
            persistence_docs, min_persisted, min_visible, include, exclude)
        if not keep_tokens:
            stats_docs = drop_tokens(stats_docs)

        if output_dir == None:
            yield from stats_docs
        else:
            new_path = files.output_dir_path(path, output_dir, compression)
            writer = files.writer(new_path)
            for rev_doc in stats_docs:
                json.dump(rev_doc, writer)
                writer.write("\n")

    for rev_doc in mwxml.map(process, paths, threads=threads):
        json.dump(rev_doc, sys.stdout)
        sys.stdout.write("\n")
