
class MockDataStorage:

    def __init__(self):
        self.added = []
        self.attachments_added = []
        self.extractions = []

    def exists(self, search_element=None):
        if search_element is not None:
            return False
        return False

    def add(self, data):
        self.added.append(data)

    def add_attachment(self, data):
        self.attachments_added.append(data)

    def add_extraction_to_database(self, *args):
        self.extractions.append(args)
