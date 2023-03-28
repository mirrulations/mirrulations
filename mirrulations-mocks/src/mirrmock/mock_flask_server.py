from fakeredis import FakeRedis, FakeServer
from mirrmock.mock_data_storage import MockDataStorage


class MockAttachmentSaver():
    def __init__(self):
        self.num_attachments = 0
        self.data = None
        self.path = None

    def save(self, data, path=None):
        self.path = path
        self.num_attachments += 1
        self.data = data


def mock_work_server(create_server):
    redis_server = FakeServer()
    mock_db = FakeRedis(server=redis_server)
    mock_saver = MockAttachmentSaver()
    server = create_server(mock_db)
    server.redis_server = redis_server
    server.app.config['TESTING'] = True
    server.client = server.app.test_client()
    server.data = MockDataStorage()
    server.attachment_saver = mock_saver
    return server
