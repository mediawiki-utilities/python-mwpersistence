from nose.tools import eq_

from ..persistence2stats import persistence2stats

test_persistence_docs = [
    {"sha1": "aaa",
     "id": 10,
     "persistence": {
         'revisions_processed': 2,
         'non_self_processed': 1,
         'seconds_possible': 2,
         'tokens': [{'text': "I", 'persisted': 2, 'non_self_persisted': 1,
                     'seconds_visible': 2},
                    {'text': " ", 'persisted': 2, 'non_self_persisted': 1,
                     'seconds_visible': 2},
                    {'text': "am", 'persisted': 2, 'non_self_persisted': 1,
                     'seconds_visible': 2},
                    {'text': " ", 'persisted': 2, 'non_self_persisted': 1,
                     'seconds_visible': 2},
                    {'text': "foo", 'persisted': 2, 'non_self_persisted': 1,
                     'seconds_visible': 2},
                    {'text': ".", 'persisted': 2, 'non_self_persisted': 1,
                     'seconds_visible': 2}]
     },
     "timestamp": "1970-01-01T00:00:00Z",
     "page": {"title": "Foo", "id": 1, "namespace": 0},
     "user": {"text": "EpochFail", "id": 6396742}},
    {"sha1": "bbb",
     "id": 11,
     "persistence": {
         'revisions_processed': 1,
         'non_self_processed': 1,
         'seconds_possible': 1,
         'tokens': [{'text': " ", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': "as", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': " ", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': "well", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1}]
     },
     "timestamp": "1970-01-01T00:00:01Z",
     "page": {"title": "Foo", "id": 1, "namespace": 0},
     "user": {"text": "127.0.0.1", "id": None}},
    {"sha1": "aaa",
     "id": 12,
     "persistence": {
         'revisions_processed': 0,
         'non_self_processed': 0,
         'seconds_possible': 0,
         'tokens': []
     },
     "timestamp": "1970-01-01T00:00:02Z",
     "page": {"title": "Foo", "id": 1, "namespace": 0},
     "user": {"text": "EpochFail", "id": 6396742}},
    {"sha1": "aaa",
     "id": 20,
     "persistence": {
         'revisions_processed': 0,
         'non_self_processed': 0,
         'seconds_possible': 1,
         'tokens': [{'text': "I", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': " ", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': "am", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': " ", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': "bar", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1},
                    {'text': ".", 'persisted': 0, 'non_self_persisted': 0,
                     'seconds_visible': 1}]
     },
     "timestamp": "1970-01-01T00:00:00Z",
     "page": {"title": "Bar", "id": 2, "namespace": 0},
     "user": {"text": "EpochFail", "id": 6396742}}
]


def test_persistence2stats():
    docs = persistence2stats(test_persistence_docs, min_persisted=2,
                              min_visible=10,
                              exclude=lambda t: len(t.strip()) == 0)

    docs = list(docs)

    eq_(docs[0]['persistence']['tokens_added'], 4)
    eq_(docs[0]['persistence']['persistent_tokens'], 4)
    eq_(docs[0]['persistence']['non_self_persistent_tokens'], 0)
    eq_(docs[0]['persistence']['censored'], True)
    eq_(docs[0]['persistence']['non_self_censored'], True)

    assert docs[0]['persistence']['sum_log_persisted'] > 0, \
           docs[0]['persistence']['sum_log_persisted']

    assert docs[0]['persistence']['sum_log_non_self_persisted'] > 0, \
           docs[0]['persistence']['sum_log_non_self_persisted']

    assert docs[0]['persistence']['sum_log_seconds_visible'] > 0, \
           docs[0]['persistence']['sum_log_seconds_visible']
