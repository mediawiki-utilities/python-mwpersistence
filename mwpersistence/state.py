import logging
from hashlib import sha1

import mwreverts

from .token import Token

logger = logging.getLogger(__name__)


class Version:
    __slots__ = ('tokens', )

    def __init__(self, tokens=None):
        self.tokens = tokens


class State:
    """
    Constructs a revision state object that will track the persistence of
    tokens though a history of revisions of word persistence.  This class is
    commonly used to process the revisions of a page in chronological order.
    """

    def update(self, text, revision=None):
        raise NotImplementedError()


class DiffState:
    """
    Constructs a state object with a diff-based transition function.

    :Parameters:
        diff_engine : :class:`deltas.DiffEngine`
            A "diff engine" processor for sequentially diffing text
        revert_radius : int
            a positive integer indicating the maximum revision distance
            that a revert can span.
        revert_detector : :class:`mwreverts.Detector`
            A revert detector.

    :Example:
        >>> import mwpersistence
        >>> import deltas
        >>>
        >>> state = mwpersistence.DiffState(deltas.SegmentMatcher())
        >>>
        >>> print(state.update("Apples are red.", revision=1))
        ([Token(text='Apples', revisions=[1]),
          Token(text=' ', revisions=[1]),
          Token(text='are', revisions=[1]),
          Token(text=' ', revisions=[1]),
          Token(text='red', revisions=[1]),
          Token(text='.', revisions=[1])],
         [Token(text='Apples', revisions=[1]),
          Token(text=' ', revisions=[1]),
          Token(text='are', revisions=[1]),
          Token(text=' ', revisions=[1]),
          Token(text='red', revisions=[1]),
          Token(text='.', revisions=[1])],
         [])
        >>> print(state.update("Apples are blue.", revision=2))
        ([Token(text='Apples', revisions=[1, 2]),
          Token(text=' ', revisions=[1, 2]),
          Token(text='are', revisions=[1, 2]),
          Token(text=' ', revisions=[1, 2]),
          Token(text='blue', revisions=[2]),
          Token(text='.', revisions=[1, 2])],
         [Token(text='blue', revisions=[2])],
         [Token(text='red', revisions=[1])])
        >>> print(state.update("Apples are red.", revision=3)) # A revert!
        ([Token(text='Apples', revisions=[1, 2, 3]),
          Token(text=' ', revisions=[1, 2, 3]),
          Token(text='are', revisions=[1, 2, 3]),
          Token(text=' ', revisions=[1, 2, 3]),
          Token(text='red', revisions=[1, 3]),
          Token(text='.', revisions=[1, 2, 3])],
         [],
         [])
    """

    class Version:
        __slots__ = ('tokens',)

        def __init__(self):
            self.tokens = None

    def __init__(self, diff_engine=None, revert_radius=None,
                 revert_detector=None):
        if diff_engine is not None:
            if not hasattr(diff_engine, 'process'):
                raise TypeError("'diff_engine' of type {0} does not have a " +
                                "process() method.".format(type(diff_engine)))
            else:
                self.diff_engine = diff_engine
                self.diff_processor = self.diff_engine.processor()
        else:
            self.diff_engine, self.diff_processor = None, None

        # Either pass a detector or the revert radius so I can make one
        if revert_detector is None and revert_radius is None:
            raise TypeError("Either a 'revert_detector' or a " +
                            "'revert_radius' must be provided.")

        if revert_detector is None:
            self.revert_detector = mwreverts.Detector(int(revert_radius))
        else:
            self.revert_detector = revert_detector

        # Stores the last tokens
        self.last = Version()

    def update(self, text, revision=None):
        """
        Modifies the internal state based a change to the content and returns
        the sets of words added and removed.

        :Parameters:
            text : str
                The text content of a revision
            revision : `mixed`
                Revision metadata

        :Returns:
            A triple of lists:

            current_tokens : `list` ( :class:`~mwpersistence.Token` )
                A sequence of Tokens representing the revision that was just
                processed.
            tokens_added : `list` ( :class:`~mwpersistence.Token` )
                Tokens that were added while updating state.
            tokens_removed : `list` ( :class:`~mwpersistence.Token` )
                Tokens that were removed while updating state.
        """
        return self._update(text=text, revision=revision)

    def update_opdocs(self, checksum, opdocs, revision=None):
        """
        Modifies the internal state based a change to the content and returns
        the sets of words added and removed.

        :Parameters:
            checksum : `hashable`
                A checksum generated from the text of a revision
            opdocs : `iterable` ( `dict` )
                A sequence of operations that represent the diff of this new
                revision
            revision : `mixed`
                Revision metadata

        :Returns:
            A triple of lists:

            current_tokens : `list` ( :class:`~mwpersistence.Token` )
                A sequence of Tokens representing the revision that was just
                processed.
            tokens_added : `list` ( :class:`~mwpersistence.Token` )
                Tokens that were added while updating state.
            tokens_removed : `list` ( :class:`~mwpersistence.Token` )
                Tokens that were removed while updating state.
        """
        return self._update(checksum=checksum, opdocs=opdocs,
                            revision=revision)

    def _update(self, text=None, checksum=None, opdocs=None, revision=None):
        if checksum is None:
            if text is None:
                raise TypeError("Either 'text' or 'checksum' must be " +
                                "specified.")
            else:
                checksum = sha1(bytes(text, 'utf8')).hexdigest()

        current_version = Version()

        revert = self.revert_detector.process(checksum, current_version)
        if revert is not None:  # Revert
            logger.debug("Revert detected between {0} and {1}"
                         .format(revert.reverting, revert.reverted_to))
            # Extract reverted_to revision
            current_version.tokens = revert.reverted_to.tokens

            # Update diff_processor state
            if self.diff_processor is not None:
                self.diff_processor.update(last_tokens=current_version.tokens)

            transition = current_version.tokens, [], []

        else:

            if opdocs is not None:
                transition = apply_opdocs(opdocs, self.last.tokens or [])
                current_version.tokens, _, _ = transition
            else:
                # NOTICE: HEAVY COMPUTATION HERE!!!
                #
                # Diffs usually run in O(n^2) -- O(n^3) time and most
                # tokenizers produce a lot of tokens.
                if self.diff_processor is None:
                    raise RuntimeError("DiffState cannot process raw text " +
                                       "without a diff_engine specified.")
                operations, _, current_tokens = \
                    self.diff_processor.process(text, token_class=Token)

                transition = apply_operations(operations,
                                              self.last.tokens or [],
                                              current_tokens)
                current_version.tokens, _, _ = transition

        # Record persistence
        persist_revision_once(current_version.tokens, revision)

        # Update last version
        self.last = current_version

        # Return the tranisitoned state
        return transition


def persist_revision_once(tokens, revision):
    """
    This function makes sure that a revision is only marked as persisting
    for a token once.  This is important since some diff algorithms allow
    tokens to be copied more than once in a revision.  The id(token) should
    unique to the in-memory representation of any object, so we use that as
    unique token instance identifier.
    """
    token_map = {id(token):token for token in tokens}
    for token in token_map.values():
        token.persist(revision)


def apply_operations(operations, a, b):
    tokens = []
    tokens_added = []
    tokens_removed = []

    for op in operations:

        if op.name in ("replace", "insert"):

            new_tokens = b[op.b1:op.b2]
            tokens.extend(new_tokens)
            tokens_added.extend(new_tokens)

        if op.name in ("replace", "delete"):
            tokens_removed.extend(a[op.a1:op.a2])

        elif op.name == "equal":
            tokens.extend(a[op.a1:op.a2])

    return (tokens, tokens_added, tokens_removed)


def apply_opdocs(op_docs, a, token_class=Token):
    tokens = []
    tokens_added = []
    tokens_removed = []

    for op_doc in op_docs:

        if op_doc['name'] in ("replace", "insert"):

            new_tokens = [token_class(s) for s in op_doc['tokens']]
            tokens.extend(new_tokens)
            tokens_added.extend(new_tokens)

        if op_doc['name'] in ("replace", "delete"):
            tokens_removed.extend(a[op_doc['a1']:op_doc['a2']])

        elif op_doc['name'] == "equal":
            tokens.extend(a[op_doc['a1']:op_doc['a2']])

    return (tokens, tokens_added, tokens_removed)
