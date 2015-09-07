import deltas


class Token(deltas.Token):
    __slots__ = ('revisions',)

    def __init__(self, content, type=None, revisions=None):
        super().__init__(self, content, type=type)

        self.revisions = revisions if revisions is not None else []
        """
        The meta data for the revisions that the token has appeared within.
        """

    def persist(self, revision):
        self.revisions.append(revision)

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return "{0}({1})".format(
            self.__class__.__name__,
            ", ".join([
                repr(str(self)),
                "type={0}".format(self.type),
                "revisions={0}".format(repr(self.revisions))
            ])
        )
