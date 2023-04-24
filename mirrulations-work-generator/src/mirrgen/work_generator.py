import os
import time
import dotenv
from mirrgen.search_iterator import SearchIterator
from mirrgen.results_processor import ResultsProcessor
from mirrcore.regulations_api import RegulationsAPI
from mirrcore.job_queue import JobQueue
from mirrcore.job_queue_exceptions import JobQueueException
from mirrcore.redis_check import load_redis
from mirrcore.data_counts import DataCounts
from mirrcore.jobs_statistics import JobStatistics
from mirrcore.bucket_size import BucketSize
from botocore.exceptions import ClientError
# pylint: disable=R0915:too-many-statements


class WorkGenerator:

    def __init__(self, job_queue, api):
        self.job_queue = job_queue
        self.api = api
        self.processor = ResultsProcessor(job_queue)

    def download(self, endpoint):
        # Gets the timestamp of the last known job in queue
        last_timestamp = self.job_queue.get_last_timestamp_string(endpoint)
        # Finds a job, from the timestamp of the last known job
        # Returns a URL for the specific element
        for result in SearchIterator(self.api, endpoint, last_timestamp):
            if result == {}:
                continue
            # If jobs are not in redis
            # add the URL to the jobs_queue (RabbitMQ)
            self.processor.process_results(result)
            timestamp = result['data'][-1]['attributes']['lastModifiedDate']
            self.job_queue.set_last_timestamp_string(endpoint, timestamp)


if __name__ == '__main__':
    # I wrapped the code in a function to avoid pylint errors
    # about shadowing api and job_queue
    def generate_work():
        # Gets an API key
        dotenv.load_dotenv()
        api_key = os.getenv('API_KEY')
        api = RegulationsAPI(api_key)

        database = load_redis()

        job_queue = JobQueue(database)

        generator = WorkGenerator(job_queue, api)

        job_stats = JobStatistics(database)

        # Save the total number of docket, document, and comment
        # entries in Regulations.gov
        regulations_data_counts = DataCounts(api_key).get_counts()
        job_stats.set_regulations_data(regulations_data_counts)

        try:
            print('BUCKET SIZE', BucketSize.get_bucket_size())
        except ClientError:
            print('error : Signature does not match')

        # Download dockets, documents, and comments
        # from all jobs in the job queue
        print('Begin generate docket jobs')
        generator.download('dockets')
        print('End generate docket jobs')
        print('Begin generate document jobs')
        generator.download('documents')
        print('End generate document jobs')
        print('Begin generate comment jobs')
        generator.download('comments')
        print('End generate comment jobs')

    while True:
        try:
            generate_work()
        except JobQueueException:
            print("FAILURE: Error occurred when adding a job. Sleeping...")
        # Sleeps for 6 hours
        time.sleep(60 * 60 * 6)
