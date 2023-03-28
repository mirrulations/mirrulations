import pymongo


class DataStorage:
    def __init__(self):
        database = pymongo.MongoClient('mongo', 27017)['mirrulations']
        self.dockets = database['dockets']
        self.documents = database['documents']
        self.comments = database['comments']
        self.attachments = database['attachments']

    def exists(self, search_element):
        result_id = search_element['id']

        return self.dockets.count_documents({'id': result_id}) > 0 or \
            self.documents.count_documents({'id': result_id}) > 0 or \
            self.comments.count_documents({'id': result_id}) > 0 or \
            self.attachments.count_documents({'id': result_id}) > 0

    def add(self, data):
        if 'type' in data['data'].keys():
            if data['data']['type'] == 'dockets':
                self.dockets.insert_one(data)
            elif data['data']['type'] == 'documents':
                self.documents.insert_one(data)
            elif data['data']['type'] == 'comments':
                self.comments.insert_one(data)

    def add_attachment(self, data):
        entry = {'path': data['attachment_path'],
                 'file': data['attachment_filename']}
        self.attachments.insert_one(entry)
