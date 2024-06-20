from datetime import datetime
import os
import time
import io
import struct
import pdfminer
import pdfminer.high_level
import pdfminer.psparser
import pikepdf
import redis
from mirrcore.path_generator import PathGenerator
from mirrcore.jobs_statistics import JobStatistics
from mirrclient.saver import Saver
from mirrclient.s3_saver import S3Saver
from mirrclient.disk_saver import DiskSaver


class Extractor:
    """
    Class containing methods to extract text from files.
    """
    @staticmethod
    def init_job_stat():
        """
        Sets up the JobStatistics class. job_stat gets used to increase cache
        of number of extractions when an extraction is successful
        """
        redis_server = redis.Redis('redis')
        job_stat = JobStatistics(redis_server)
        Extractor.job_stat = job_stat

    @staticmethod
    def extract_text(attachment_path, save_path):
        """
        This method takes a complete path to an attachment and determines
        which type of extraction will take place.
        *Note* save_path is for later use when saving the extracted text
        Parameters
        ----------
        attachment_path : str
            the complete file path for the attachment that is being extracted
            ex. /path/to/pdf/attachment_1.pdf
        save_path : str
            the complete path to store the extract text
            ex. /path/to/text/attachment_1.txt
        """
        # gets the type of the attachment file
        #   (ex. /path/to/pdf/attachment_1.pdf -> pdf)
        file_type = attachment_path[attachment_path.rfind('.')+1:]
        if file_type.endswith('pdf'):
            print(f"Extracting text from {attachment_path}")
            text = Extractor._extract_pdf(attachment_path)
            Extractor.save_text(text, save_path)
        else:
            print("FAILURE: attachment doesn't have appropriate extension",
                  attachment_path)

    @staticmethod
    def _extract_pdf(attachment_path):
        """
        This method takes a complete path to a pdf and stores
        the extracted text in the save_path.
        *Note* If a file exists at save_path, it will be overwritten.
        Parameters
        ----------
        attachment_path : str
            the complete file path for the attachment that is being extracted
            ex. /path/to/pdf/attachment_1.pdf
        """
        try:
            pdf = pikepdf.open(attachment_path)
            pdf_bytes = io.BytesIO()
            pdf.save(pdf_bytes)
            return pdfminer.high_level.extract_text(pdf_bytes)
        except (ValueError, TypeError, struct.error,
                AssertionError, KeyError, pdfminer.psparser.PSSyntaxError,
                RuntimeError, pikepdf.PdfError, pikepdf.PasswordError) as err:
            print("FAILURE: failed to extract "
                  f"text from {attachment_path}\n{err}")
            return "ERROR"

    @staticmethod
    def save_text(text, save_path):
        """
        Save the text.

        @param text: the text to save
        @param save_path: str the path where we save
            the complete path to store the extract text
            ex. /path/to/text/attachment_1.txt
        @return: None
        """

        # Save the extracted text to a file
        saver = Saver([DiskSaver(), S3Saver("mirrulations")])
        saver.save_text(save_path, text.strip())
        print(f"SUCCESS: Saved extraction at {save_path}")

    @staticmethod
    def update_stats():
        """
        Update the redis stats
        @return: None
        """
        try:
            Extractor.job_stat.increase_extractions_done()
        except redis.ConnectionError as error:
            print(f"Couldn't increase extraction cache number due to: {error}")


if __name__ == '__main__':
    Extractor.init_job_stat()
    now = datetime.now()
    while True:
        for (root, dirs, files) in os.walk('/data'):
            for file in files:
                # Checks for pdfs
                if not file.endswith('pdf'):
                    continue
                complete_path = os.path.join(root, file)
                output_path = PathGenerator\
                    .make_attachment_save_path(complete_path)
                if not os.path.isfile(output_path):
                    # Write an empty file.  The extract_text method sometimes
                    # fails with an out-of-memory error if the file is too
                    # large, and a restart would try again.  This ensures
                    # that the extraction is not attempted again when the
                    # extractor process is restarted (by Docker).
                    with open(output_path, 'w') as f:
                        pass
                    start_time = time.time()
                    Extractor.extract_text(complete_path, output_path)
                    print(f"Time taken to extract text from {complete_path}"
                          f" is {time.time() - start_time} seconds")
                    Extractor.update_stats()
        # sleep for a hour
        current_time = now.strftime("%H:%M:%S")
        print(f"Sleeping for one hour : started at {current_time}")
        time.sleep(3600)
