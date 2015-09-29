from nose.tools import eq_

from ..token import Token


def test_token():
    t = Token("foo")
    eq_(t.revisions, [])

    t.persist(1)
    t.persist(2)
    eq_(t.revisions, [1, 2])
