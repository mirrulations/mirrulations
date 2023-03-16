import os
import time
import dotenv
import redis
from mirrgen.search_iterator import SearchIterator
from mirrgen.results_processor import ResultsProcessor
from mirrcore.regulations_api import RegulationsAPI
from mirrcore.job_queue import JobQueue
from mirrcore.data_storage import DataStorage
from mirrcore.redis_check import is_redis_available


class WorkGenerator:

    def __init__(self, job_queue, api, datastorage):
        self.job_queue = job_queue
        self.api = api
        self.processor = ResultsProcessor(job_queue, datastorage)

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
        api = RegulationsAPI(os.getenv('API_KEY'))

        # Checks if redis database is available
        database = redis.Redis('redis')
        # Sleep for 30 seconds to give time to load
        while not is_redis_available(database):
            print("Redis database is busy loading")
            time.sleep(30)

        job_queue = JobQueue(database)

        storage = DataStorage()

        generator = WorkGenerator(job_queue, api, storage)

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
        generate_work()
        # Sleeps for 6 hours
        time.sleep(60 * 60 * 6)
