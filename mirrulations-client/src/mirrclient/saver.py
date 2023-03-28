import os
from json import dumps, load
import pymongo


class Saver:
    """
    A class which takes the content of an attachment (pdf, doc, etc.), and
    saves it to a given path.
    ...
    Methods
    -------
    save(content = response, path = string)
        Takes the content (pdf, doc, etc.) and saves the attachment to a
        given path
    """

    def __init__(self):
        database = pymongo.MongoClient('mongo', 27017)['mirrulations']
        self.dockets = database['dockets']
        self.documents = database['documents']
        self.comments = database['comments']
        self.attachments = database['attachments']

    def make_path(self, path):
        try:
            os.makedirs(f'/data{path}')
        except FileExistsError:
            print(f'Directory already exists in root: /data{path}')

    def save_to_disk(self, path, data):
        with open(path, 'x', encoding='utf8') as file:
            print('Writing results to disk')
            file.write(dumps(data))

    def save_json(self, path, data):
        """
        writes the results to disk. used by docket document and comment jobs

        Parameters
        ----------
        data : dict
            the results data to be written to disk
        """
        data = data['results']
        if os.path.exists(path) is False:
            self.save_to_disk(path, data)
        else:
            self.check_for_duplicates(path, data, 1)

    def save_duplicate_json(self, path, data, i):
        path_without_file_type = path.strip(".json")
        path = f'{path_without_file_type}({i}).json'
        if os.path.exists(path) is False:
            print(f'JSON is different than duplicate: Labeling ({i})')
            self.save_to_disk(path, data)
        else:
            self.check_for_duplicates(path, data, i + 1)

    def save_attachment(self, path, data):
        with open(path, "wb") as file:
            file.write(data)
            file.close()

    def open_json_file(self, path):
        with open(path, encoding='utf8') as file:
            saved_data = load(file)
        return saved_data

    def is_duplicate(self, existing, new):
        if existing == new:
            print('Data is a duplicate, skipping this download')
            return True
        return False

    def check_for_duplicates(self, path, data, i):
        if self.is_duplicate(self.open_json_file(path), data) is False:
            self.save_duplicate_json(path, data, i)

    # Mongo Saving  
    # Just a skeleton for now still need to implement
    def exists(self, search_element):
        result_id = search_element['id']

        return self.dockets.count_documents({'id': result_id}) > 0 or \
            self.documents.count_documents({'id': result_id}) > 0 or \
            self.comments.count_documents({'id': result_id}) > 0 or \
            self.attachments.count_documents({'id': result_id}) > 0

    def save_to_mongo(self, data):
        if 'type' in data['data'].keys():
            if data['data']['type'] == 'dockets':
                self.dockets.insert_one(data)
            elif data['data']['type'] == 'documents':
                self.documents.insert_one(data)
            elif data['data']['type'] == 'comments':
                self.comments.insert_one(data)
            elif data['data']['type'] == 'attachments':
                entry = {'path': data['attachment_path'], 
                         'file': data['attachment_filename']}
                self.attachments.insert_one(entry)
