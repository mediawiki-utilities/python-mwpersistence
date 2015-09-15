from deltas import SegmentMatcher
from mwtypes import Timestamp
from mwxml import Dump, Page, Revision
from nose.tools import eq_

from ..dump2diffs import dump2diffs

test_pages = [
    Page(id=1, title="Foo", namespace=0,
         revisions=iter([Revision(id=10, text="I am foo.", sha1="aaa",
                                  timestamp=Timestamp(0)),
                         Revision(id=11, text="I am foo as well.", sha1="bbb",
                                  timestamp=Timestamp(1)),
                         Revision(id=12, text="I am foo.", sha1="aaa",
                                  timestamp=Timestamp(2))])),
    Page(id=2, title="Bar", namespace=0,
         revisions=iter([Revision(id=20, text="I am bar.", sha1="aaa",
                                  timestamp=Timestamp(0))])),
    Page(id=3, title="EpochFail", namespace=2,
         revisions=iter([Revision(id=30, text="I am EpochFail", sha1="aaa",
                                  timestamp=Timestamp(0))]))
]
test_dump = Dump(site_info=None,
                 pages=iter(test_pages))


def test_dump2diffs():

    docs = dump2diffs(test_dump, SegmentMatcher(), namespaces={0})

    docs = list(docs)

    eq_(docs[0]['id'], 10)
    eq_(docs[0]['diff']['ops'],
        [{'name': "insert", 'a1': 0, 'a2': 0, 'b1': 0, 'b2': 6,
          'tokens': ["I", " ", "am", " ", "foo", "."]}])

    eq_(docs[1]['id'], 11)
    eq_(docs[2]['id'], 12)

    eq_(docs[3]['id'], 20)
    eq_(docs[3]['diff']['ops'],
        [{'name': "insert", 'a1': 0, 'a2': 0, 'b1': 0, 'b2': 6,
          'tokens': ["I", " ", "am", " ", "bar", "."]}])

    eq_(len(docs), 4)
