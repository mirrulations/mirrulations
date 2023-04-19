import os
from json import dumps, load


class DiskSaver():

    def make_path(self, _dir):
        try:
            os.makedirs(_dir)
        except FileExistsError:
            print(f'Directory already exists in root: /data{_dir}')

    def save_to_disk(self, path, data):
        with open(path, 'x', encoding='utf8') as file:
            file.write(dumps(data))
            print(f'Wrote json to Disk: {path}')

    def save_json(self, path, data):
        """
        writes the results to disk. used by docket document and comment jobs
        Parameters
        ----------
        data : dict
            the results data to be written to disk
        """
        _dir = path.rsplit('/', 1)[0]
        self.make_path(_dir)
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

    def save_binary(self, path, data):
        _dir = path.rsplit('/', 1)[0]
        self.make_path(_dir)
        with open(path, "wb") as file:
            file.write(data)
            file.close()
            print(f'Wrote binary to Disk: {path}')

    def save_text(self, path, data):
        _dir = path.rsplit('/', 1)[0]
        self.make_path(_dir)
        with open(path, "w", encoding="utf-8") as file:
            file.write(data)
            file.close()
            print(f'Wrote extracted text to Disk: {path}')

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

    def get_extracted_text_attachments_dir(self, path):
        # remove file name from path
        path = path.rsplit("/", 1)[0]
        return path.replace('comments_extracted_text/pdfminer',
                            'comments_attachments/').replace('text', 'binary')

    def generate_metadata_for_extraction(self, path):
        # comments_extracted_text structure
        # data/data/EPA/EPA-HQ-OA-2003-0001/text-EPA-HQ-OA-2003-0001/comments_extracted_text/pdfminer/
        # Attachments directory for given comment
        # data/data/EPA/EPA-HQ-OA-2003-0001/binary-EPA-HQ-OA-2003-0001/comments_attachments

        docket_id = path.rsplit("/comments_extracted_text", 1)[0]\
            .split("text-")[-1]

        attachments_dir = self.get_extracted_text_attachments_dir(path)
        extracted_dir = path.rsplit("/", 1)[0]
        pdf_files = [f for f in os.listdir(attachments_dir) if ".pdf" in f]
        extracted_txt_files = [file for file in os.listdir(extracted_dir)
                               if ".txt" in file]
        meta = {
            "DocketID": docket_id,
            "ExtractedPDFSCompleted":
                len(extracted_txt_files),
            "TotalPDFs": len(pdf_files),
            "Failed/IncompleteExtractions":
                len(pdf_files) - len(extracted_txt_files),
            "PercentComplete":
                len(extracted_txt_files)/len(pdf_files) * 100
        }
        return meta

    def save_extraction_meta(self, path):
        meta = self.generate_metadata_for_extraction(path)
        meta_save_dir = f'{path.rsplit("/", 1)[0]}/meta.json'
        with open(f"{meta_save_dir}", 'w', encoding='utf8') as file:
            file.write(dumps(meta))
            print(f'Wrote Extraction Metadata to Disk: {meta_save_dir}')
