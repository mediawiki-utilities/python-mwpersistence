from nose.tools import eq_

from ..diffs2persistence import diffs2persistence

test_diff_docs = [
    {"sha1": "aaa",
     "id": 10,
     "diff": {"last_id": None,
              "ops": [{"a2": 0, "name": "insert", "a1": 0, "b1": 0, "b2": 6,
                       "tokens": ["I", " ", "am", " ", "foo", "."]}]},
     "timestamp": "1970-01-01T00:00:00Z",
     "page": {"title": "Foo", "id": 1, "namespace": 0},
     "user": {"text": "EpochFail", "id": 6396742},
     "format": None},
    {"sha1": "bbb",
     "id": 11,
     "diff": {"last_id": 10,
              "ops": [{"a2": 5, "b1": 0, "a1": 0, "name": "equal", "b2": 5},
                      {"a2": 5, "name": "insert", "a1": 5, "b1": 5, "b2": 9,
                       "tokens": [" ", "as", " ", "well"]},
                      {"a2": 6, "b1": 9, "a1": 5, "name": "equal", "b2": 10}]},
     "timestamp": "1970-01-01T00:00:01Z",
     "page": {"title": "Foo", "id": 1, "namespace": 0},
     "user": {"text": "127.0.0.1", "id": None}},
    {"sha1": "aaa",
     "id": 12,
     "diff": {"last_id": 11,
              "ops": [{"a2": 5, "b1": 0, "a1": 0, "name": "equal", "b2": 5},
                      {"a2": 9, "name": "delete", "a1": 5, "b1": 5, "b2": 5,
                       "tokens": [" ", "as", " ", "well"], },
                      {"a2": 10, "b1": 5, "a1": 9, "name": "equal", "b2": 6}]},

     "timestamp": "1970-01-01T00:00:02Z",
     "page": {"title": "Foo", "id": 1, "namespace": 0},
     "user": {"text": "EpochFail", "id": 6396742}},
    {"sha1": "aaa",
     "id": 20,
     "diff": {"last_id": None,
              "ops": [{"a2": 0, "name": "insert", "a1": 0, "b1": 0, "b2": 6,
                       "tokens": ["I", " ", "am", " ", "bar", "."]}]},
     "timestamp": "1970-01-01T00:00:00Z",
     "page": {"title": "Bar", "id": 2, "namespace": 0},
     "user": {"text": "EpochFail", "id": 6396742}}
]


def test_diffs2persistence():
    docs = diffs2persistence(test_diff_docs)

    docs = list(docs)

    eq_([t['text'] for t in docs[0]['persistence']['tokens']],
        ["I", " ", "am", " ", "foo", "."])
    eq_(docs[0]['persistence']['revisions_processed'], 2)

    eq_([t['persisted'] for t in docs[0]['persistence']['tokens']],
        [2, 2, 2, 2, 2, 2])

    eq_([t['non_self_persisted'] for t in docs[0]['persistence']['tokens']],
        [1, 1, 1, 1, 1, 1])

    eq_([t['persisted'] for t in docs[1]['persistence']['tokens']],
        [0, 0, 0, 0])

    eq_([t['persisted'] for t in docs[2]['persistence']['tokens']],
        [])

    eq_([t['persisted'] for t in docs[3]['persistence']['tokens']],
        [0, 0, 0, 0, 0, 0])
    eq_(docs[3]['persistence']['revisions_processed'], 0)
