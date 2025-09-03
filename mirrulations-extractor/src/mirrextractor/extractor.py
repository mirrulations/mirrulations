from datetime import datetime
import os
import time
import redis
from mirrcore.path_generator import PathGenerator
from mirrcore.jobs_statistics import JobStatistics


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
        This method is a stub - PDF extraction functionality has been removed.
        
        Parameters
        ----------
        attachment_path : str
            the complete file path for the attachment that is being extracted
        save_path : str
            the complete path to store the extract text
        """
        print(f"PDF extraction disabled. Skipping {attachment_path}")
        # Create empty file to mark as processed
        with open(save_path, 'w') as f:
            f.write('PDF extraction disabled')


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
                    # Write an empty file to mark as processed
                    # PDF extraction has been disabled
                    with open(output_path, 'w') as f:
                        f.write('PDF extraction disabled')
                    start_time = time.time()
                    Extractor.extract_text(complete_path, output_path)
                    print(f"Time taken to process {complete_path}"
                          f" is {time.time() - start_time} seconds")
                    Extractor.update_stats()
        # sleep for a hour
        current_time = now.strftime("%H:%M:%S")
        print(f"Sleeping for one hour : started at {current_time}")
        time.sleep(3600)
