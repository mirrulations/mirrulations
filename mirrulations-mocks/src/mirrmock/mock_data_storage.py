
class MockDataStorage:

    def __init__(self):
        self.added = []
        self.attachments_added = []

    # pylint: disable=unused-argument, no-self-use
    def exists(self, search_element):
        return False

    def add(self, data):
        self.added.append(data)

    def add_attachment(self, data):
        self.attachments_added.append(data)
