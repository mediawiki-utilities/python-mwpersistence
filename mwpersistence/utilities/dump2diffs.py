r"""
``$ mwpersistence dump2diffs -h``
::

    Computes diffs from an XML dump.  This script expects either be
    given a decompressed dump to <stdin> (single thread) or to have
    <dump file>s specified as command-line arguments (multi-threaded).

    If no <dump files>s are specified, this script expects to read a
    decompressed dump from <stdin>.

    $ bzcat dump.xml.bz2 | dump2diffs --config=conf.yaml > diffs.json

    In the case that <dump files>s are specified, this utility can process them
    multi-threaded.  You can customize the number of parallel `--threads`.

    $ dump2diffs pages-meta-history*.xml.bz2 --config=conf.yaml > diffs.json

    Usage:
        dump2diffs (-h|--help)
        dump2diffs [<dump_file>...] --config=<path> [--namespaces=<ids>]
                   [--timeout=<secs>] [--keep-text] [--threads=<num>]
                   [--output=<path>] [--compress=<type>] [--verbose]

    Options:
        -h|--help           Print this documentation
        <dump-file>         The path to a MediaWiki XML Dump file
                            [default: <stdin>]
        --config=<path>     The path to a deltas DiffEngine configuration
        --namespaces=<ids>  A comma separated list of namespace IDs to be
                            considered [default: <all>]
        --timeout=<secs>    The maximum number of seconds that a diff will be
                            able to run before being stopped [default: 10]
        --keep-text         If set, the 'text' field will be populated in the
                            output JSON.
        --threads=<num>     If a collection of files are provided, how many
                            processor threads? [default: <cpu_count>]
        --output=<path>     Write output to a directory with one output file
                            per input path.  [default: <stdout>]
        --compress=<type>   If set, output written to the output-dir will be
                            compressed in this format. [default: bz2]
        --verbose           Print progress information to stderr.  Kind of a
                            mess when running multi-threaded.
"""
import json
import logging
import sys
import time
from multiprocessing import cpu_count

import docopt
import mwxml
import yamlconf
from deltas import DiffEngine
from stopit import ThreadingTimeout as Timeout
from stopit import TimeoutException

from .. import files
from .util import drop_text, ops2opdocs, revision2doc

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

    diff_engine, namespaces, timeout, keep_text = process_args(args)

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

    verbose = bool(args['--verbose'])

    run(paths, diff_engine, namespaces, timeout, keep_text, threads,
        output_dir, compression, verbose)


def process_args(args):
    config_doc = yamlconf.load(open(args['--config']))
    diff_engine = DiffEngine.from_config(config_doc, config_doc['diff_engine'])

    if args['--namespaces'] == "<all>":
        namespaces = None
    else:
        namespaces = set(int(id)
                         for id in args['--namespaces'].strip().split(","))

    timeout = float(args['--timeout'])

    keep_text = bool(args['--keep-text'])

    return diff_engine, namespaces, timeout, keep_text


def run(paths, diff_engine, namespaces, timeout, keep_text, threads,
        output_dir, compression, verbose):

    def process(dump, path):
        rev_docs = dump2diffs(dump, diff_engine, namespaces=namespaces,
                              timeout=timeout, verbose=verbose)

        if not keep_text:
            rev_docs = drop_text(rev_docs)

        if output_dir == None:
            yield from rev_docs
        else:
            new_path = files.output_dir_path(path, output_dir, compression)
            writer = files.writer(new_path)
            for rev_doc in rev_docs:
                json.dump(rev_doc, writer)
                writer.write("\n")

    for rev_doc in mwxml.map(process, paths, threads=threads):
        json.dump(rev_doc, sys.stdout)
        sys.stdout.write("\n")


def dump2diffs(dump, diff_engine, namespaces=None, timeout=None,
               verbose=False):
    """
    Generates a sequence of revision JSON documents containing a 'diff' field
    that represents the change to the text between revisions.

    :Parameters:
        diff_engine : :class:`deltas.DiffEngine`
            A configured diff engine for comparing revisions
        namespaces : `set` ( `int` )
            A set of namespace IDs that will be processed.  If left
            unspecified, all namespaces will be processed.
        timeout : `float`
            The maximum time in seconds that a difference detection operation
            should be allowed to consume.  This is used to handle extremely
            computationally complex diffs that occur from time to time.  When
            a diff takes longer than this many seconds, a trivial diff will be
            reported (remove all the tokens and add them back) and the
            'timedout' field will be set to True
        verbose : `bool`
            Print dots and stuff to stderr
    """
    namespaces = set(namespaces) if namespaces is not None else None

    for page in dump:
        if namespaces is not None and page.namespace not in namespaces:
            # Skip this entire page.
            continue

        if verbose:
            sys.stderr.write(page.title + ": ")

        processor = diff_engine.processor()
        for rev_doc in diff_revisions(page, processor, timeout=timeout):

            if verbose:
                if rev_doc['diff']['ops'] is not None:
                    sys.stderr.write(".")
                else:
                    sys.stderr.write("T")
                sys.stderr.flush()

            yield rev_doc

        if verbose:
            sys.stderr.write("\n")


def diff_revisions(page, processor, last_id=None, timeout=None):

    for revision in page:
        diff = {'last_id': last_id}
        text = revision.text or ""

        # Diff processing uses a lot of CPU.  So we set a timeout for
        # crazy revisions and record a timer for analysis later.
        with Timer() as t:
            if timeout is None:
                # Just process the text
                operations, a, b = processor.process(text)
                diff['ops'] = [op for op in ops2opdocs(operations, a, b)]
            else:
                # Try processing with a timeout
                try:
                    with Timeout(timeout) as ctx:
                        operations, a, b = processor.process(text)
                except TimeoutException:
                    pass

                if ctx.state != ctx.TIMED_OUT:
                    # We didn't timeout.  cool.
                    diff['ops'] = [op for op in ops2opdocs(operations, a, b)]
                    diff['timedout'] = False
                else:
                    # We timed out.  Record a giant delete and insert
                    diff['ops'] = [
                        {
                            'name': "delete",
                            'a1': 0,
                            'a2': len(a),
                            'b1': 0,
                            'b2': 0,
                            'tokens': a
                        },
                        {
                            'name': "insert",
                            'a1': 0,
                            'a2': 0,
                            'b1': 0,
                            'b2': len(b),
                            'tokens': b
                        }
                    ]
                    diff['timedout'] = True

                    # Make sure that the processor state is right
                    processor.update(last_text=(text))

        # All done.  Record how much time it all took
        diff['time'] = t.interval

        rev_doc = revision2doc(revision, page)

        rev_doc['diff'] = diff

        yield rev_doc

        last_id = rev_doc['id']


class Timer:
    """
    From:
    http://preshing.com/20110924/timing-your-code-using-pythons-with-statement/
    """
    def __enter__(self):
        self.start = time.clock()
        self.interval = None
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
