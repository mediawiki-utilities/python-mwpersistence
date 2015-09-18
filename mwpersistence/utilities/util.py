def drop_diff(rev_docs):
    for rev_doc in rev_docs:
        del rev_doc['diff']
        yield rev_doc


def drop_text(rev_docs):
    for rev_doc in rev_docs:
        del rev_doc['text']
        yield rev_doc


def drop_tokens(rev_docs):
    for rev_doc in rev_docs:
        del rev_doc['persistence']['tokens']
        yield rev_doc


def ops2opdocs(operations, a, b):
    for operation in operations:
        yield op2doc(operation, a, b)


def op2doc(operation, a, b):

    name, a1, a2, b1, b2 = operation
    doc = {
        'name': name,
        'a1': a1,
        'a2': a2,
        'b1': b1,
        'b2': b2
    }
    if name == "insert":
        doc['tokens'] = b[b1:b2]
    elif name == "delete":
        doc['tokens'] = a[a1:a2]

    return doc


def revision2doc(revision, page):
    rev_doc = revision.to_json()
    rev_doc['page'] = page.to_json()
    return rev_doc


def normalize_doc(rev_doc):
    if 'contributor' in rev_doc:
        contributor_doc = rev_doc['contributor'] or {}
        user_doc = {'id': contributor_doc.get('id'),
                    'text': contributor_doc.get('user_text')}

        rev_doc['user'] = user_doc

    return rev_doc
