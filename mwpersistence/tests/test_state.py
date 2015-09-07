import deltas
from nose.tools import eq_

from ..state import DiffState


def test_diff_state():
    text_revisions = [
        ("Apples are red.", 0),
        ("Apples are blue.", 1),
        ("Apples are red.", 2),
        ("Apples are tasty and red.", 3),
        ("Apples are tasty and blue.", 4)
    ]

    state = DiffState(deltas.SegmentMatcher(), revert_radius=15)

    token_sets = []
    for text, revision in text_revisions:
        token_sets.append(state.update(text, revision))

    for i, (text, revision) in enumerate(text_revisions):
        eq_("".join(token_sets[i][0]), text)

    eq_(token_sets[0][0][0], "Apples")
    eq_(len(token_sets[0][0][0].revisions), 5)
    eq_(token_sets[0][0][4], "red")
    eq_(len(token_sets[0][0][4].revisions), 3)


def test_diff_state_incrementally():

    state = DiffState(deltas.SegmentMatcher(), revert_radius=15)

    tokens, added, removed = state.update("Apples are red.", revision=0)
    eq_(tokens, ["Apples", " ", "are", " ", "red", "."])
    eq_(added, ["Apples", " ", "are", " ", "red", "."])
    eq_(removed, [])

    tokens, added, removed = state.update("Apples are blue.", revision=0)
    eq_(tokens, ["Apples", " ", "are", " ", "blue", "."])
    eq_(added, ["blue"])
    eq_(removed, ["red"])

    tokens, added, removed = state.update("Apples are red.", revision=0)
    eq_(tokens, ["Apples", " ", "are", " ", "red", "."])
    eq_(added, [])
    eq_(removed, [])

    tokens, added, removed = state.update("Apples are tasty and red.", revision=1)
    eq_(tokens, ["Apples", " ", "are", " ", "tasty", " ", "and", " ", "red",
                 "."])
    eq_(added, ["tasty", " ", "and", " "])
    eq_(removed, [])

    tokens, added, removed = state.update("Apples are tasty and blue.", revision=1)
    eq_(tokens, ["Apples", " ", "are", " ", "tasty", " ", "and", " ", "blue",
                 "."])
    eq_(added, ["blue"])
    eq_(removed, ["red"])