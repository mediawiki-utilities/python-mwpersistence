from nose.tools import eq_

from ..token import Token


def test_token():
    t = Token("foo")
    eq_(t.revisions, [])
