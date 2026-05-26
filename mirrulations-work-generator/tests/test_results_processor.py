import json
import os
from fakeredis import FakeRedis
from mirrgen.results_processor import (
    ResultsProcessor,
    job_url_from_listing_item,
    print_report,
)
from mirrcore.job_queue import JobQueue
from mirrmock.mock_dataset import MockDataSet
from mirrmock.mock_rabbitmq import MockRabbit


def test_process_results():
    database = FakeRedis()

    dir_path = os.path.dirname(os.path.realpath(__file__))

    queue = JobQueue(database)
    # mock out the rabbit connection
    queue.rabbitmq = MockRabbit()
    processor = ResultsProcessor(queue)
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
    processor = ResultsProcessor(queue)
    processor.process_results(json.loads(results[0]['text']))
    assert queue.get_num_jobs() == 1


def test_print_counts(capsys):
    print_report({'docket': 250})
    captured = capsys.readouterr()
    assert captured.out == 'Added docket: 250\n'


def test_job_url_from_listing_item_comment():
    item = {
        'id': 'FMCSA-2026-0958-0393',
        'type': 'comments',
        'attributes': {},
    }
    assert job_url_from_listing_item(item) == (
        'https://api.regulations.gov/v4/comments/FMCSA-2026-0958-0393'
        '?include=attachments')


def test_job_url_from_listing_item_docket():
    item = {'id': 'ED-2021-SCC-0032', 'type': 'dockets', 'attributes': {}}
    assert job_url_from_listing_item(item) == (
        'https://api.regulations.gov/v4/dockets/ED-2021-SCC-0032')


def test_process_results_without_links():
    database = FakeRedis()
    queue = JobQueue(database)
    queue.rabbitmq = MockRabbit()
    processor = ResultsProcessor(queue)
    listing = {
        'data': [
            {
                'id': 'FMCSA-2026-0958-0393',
                'type': 'comments',
                'attributes': {
                    'lastModifiedDate': '2026-05-15T22:07:38Z',
                },
            },
            {
                'id': 'ED-2021-SCC-0032',
                'type': 'dockets',
                'attributes': {
                    'lastModifiedDate': '2021-05-10T07:48:24Z',
                },
            },
        ],
    }
    processor.process_results(listing)

    assert queue.get_num_jobs() == 2
    assert queue.rabbitmq.jobs[0]['url'] == (
        'https://api.regulations.gov/v4/comments/FMCSA-2026-0958-0393'
        '?include=attachments')
    assert queue.rabbitmq.jobs[0]['job_type'] == 'comments'
    assert queue.rabbitmq.jobs[1]['url'] == (
        'https://api.regulations.gov/v4/dockets/ED-2021-SCC-0032')
    assert queue.rabbitmq.jobs[1]['job_type'] == 'dockets'
