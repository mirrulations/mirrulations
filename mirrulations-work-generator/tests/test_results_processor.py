import json
import os
from fakeredis import FakeRedis
from mirrgen.results_processor import ResultsProcessor, print_report
from mirrcore.job_queue import JobQueue
from mirrmock.mock_data_storage import MockDataStorage
from mirrmock.mock_dataset import MockDataSet
from mirrmock.mock_rabbitmq import MockRabbit


def test_process_results():
    database = FakeRedis()

    dir_path = os.path.dirname(os.path.realpath(__file__))

    queue = JobQueue(database)
    # mock out the rabbit connection
    queue.rabbitmq = MockRabbit()
    processor = ResultsProcessor(queue, MockDataStorage())
    with open(f'{dir_path}/data/dockets_listing.json',
              encoding='utf8') as listings:
        data = listings.read()
        processor.process_results(json.loads(data))

    assert queue.get_num_jobs() == 10


def test_job_is_added():
    database = FakeRedis()
    results = MockDataSet(1, job_type='dockets').get_results()
    queue = JobQueue(database)
    # mock out the rabbit connection
    queue.rabbitmq = MockRabbit()
    processor = ResultsProcessor(queue, MockDataStorage())
    processor.process_results(json.loads(results[0]['text']))
    assert queue.get_num_jobs() == 1


def test_print_counts(capsys):
    print_report({'docket': 250})
    captured = capsys.readouterr()
    assert captured.out == 'Added docket: 250\n'
