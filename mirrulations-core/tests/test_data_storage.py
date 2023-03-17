
from mirrcore.data_storage import DataStorage


def exists(storage, the_id):
    assert storage.exists({'id': the_id})


def does_not_exist(storage, the_id):
    assert storage.exists({'id': the_id}) is False


class FindOnly:
    def __init__(self, value):
        self.value = value

    def count_documents(self, search):
        if search['id'] == self.value:
            return 1
        return 0


class MockDB:
    def __init__(self):
        self.saved = []

    def insert_one(self, data):
        self.saved.append(data)


def test_docket_found_others_not(monkeypatch):
    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', FindOnly('DOCK-2020-1234'))
    monkeypatch.setattr(storage, 'documents', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'comments', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'attachments', FindOnly('NOTHING'))


    # docket exists
    exists(storage, 'DOCK-2020-1234')
    # document does not exist
    does_not_exist(storage, 'DOC-2020-1234')
    # comment does not exist
    does_not_exist(storage, 'COM-2020-1234')


def test_document_found_others_not(monkeypatch):
    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'documents', FindOnly('DOC-2020-1234'))
    monkeypatch.setattr(storage, 'comments', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'attachments', FindOnly('NOTHING'))
 

    # docket does not exists
    does_not_exist(storage, 'DOCK-2020-1234')
    # document does exist
    exists(storage, 'DOC-2020-1234')
    # comment does not exist
    does_not_exist(storage, 'COM-2020-1234')


def test_comment_found_others_not(monkeypatch):
    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'documents', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'comments', FindOnly('COM-2020-1234'))
    monkeypatch.setattr(storage, 'attachments', FindOnly('NOTHING'))


    # docket does not exist
    does_not_exist(storage, 'DOCK-2020-1234')

    # document does not exist
    does_not_exist(storage, 'DOC-2020-1234')

    # comment exists
    exists(storage, 'COM-2020-1234')


def test_attachment_found_others_not(monkeypatch):
    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'documents', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'comments', FindOnly('NOTHING'))
    monkeypatch.setattr(storage, 'attachments', FindOnly('ATTCH-2020-1234'))


    # docket does not exist
    does_not_exist(storage, 'DOCK-2020-1234')

    # document does not exist
    does_not_exist(storage, 'DOC-2020-1234')

    # attachment exists
    exists(storage, 'ATTCH-2020-1234')


def test_add_docket(monkeypatch):

    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', MockDB())
    monkeypatch.setattr(storage, 'documents', MockDB())
    monkeypatch.setattr(storage, 'comments', MockDB())
    monkeypatch.setattr(storage, 'attachments', MockDB())


    to_insert = {
        'data': {
            'id': 'DOCK-2020-1234',
            'type': 'dockets'
        }
    }

    storage.add(to_insert)

    assert len(storage.dockets.saved) == 1
    assert len(storage.documents.saved) == 0
    assert len(storage.comments.saved) == 0
    assert len(storage.attachments.saved) == 0



def test_add_documents(monkeypatch):

    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', MockDB())
    monkeypatch.setattr(storage, 'documents', MockDB())
    monkeypatch.setattr(storage, 'comments', MockDB())
    monkeypatch.setattr(storage, 'attachments', MockDB())


    to_insert = {
        'data': {
            'id': 'DOC-2020-1234',
            'type': 'documents'
        }
    }

    storage.add(to_insert)

    assert len(storage.dockets.saved) == 0
    assert len(storage.documents.saved) == 1
    assert len(storage.comments.saved) == 0


def test_add_comment(monkeypatch):

    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', MockDB())
    monkeypatch.setattr(storage, 'documents', MockDB())
    monkeypatch.setattr(storage, 'comments', MockDB())
    monkeypatch.setattr(storage, 'attachments', MockDB())


    to_insert = {
        'data': {
            'id': 'COMM-2020-1234',
            'type': 'comments'
        }
    }

    storage.add(to_insert)

    assert len(storage.dockets.saved) == 0
    assert len(storage.documents.saved) == 0
    assert len(storage.comments.saved) == 1


def test_add_attachment(monkeypatch):

    storage = DataStorage()

    monkeypatch.setattr(storage, 'dockets', MockDB())
    monkeypatch.setattr(storage, 'documents', MockDB())
    monkeypatch.setattr(storage, 'comments', MockDB())
    monkeypatch.setattr(storage, 'attachments', MockDB())


    to_insert = {
        'data': {
            'id': 'COMM-2020-1234',
            'attachments_text': ['foo']
        },
        'agency': 'EPA',
        'reg_id': 'AAAA',
        'results': {'file', 'file'},
        'attachment_path':"attachment_path", 
        'attachment_filename':"attachment_filename.pdf"
    }

    storage.add_attachment(to_insert)

    assert len(storage.dockets.saved) == 0
    assert len(storage.documents.saved) == 0
    assert len(storage.comments.saved) == 0
    assert len(storage.attachments.saved) == 1
