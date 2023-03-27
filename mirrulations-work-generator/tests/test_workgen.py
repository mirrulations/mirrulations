from fakeredis import FakeRedis
from mirrcore.job_queue import JobQueue
from mirrcore.job_queue_exceptions import JobQueueException
from mirrcore.regulations_api import RegulationsAPI
from mirrmock.mock_dataset import MockDataSet
from mirrmock.mock_data_storage import MockDataStorage
from mirrmock.mock_rabbitmq import MockRabbit
from mirrgen.work_generator import WorkGenerator
import pytest


def test_work_generator_single_page(requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(150).get_results()
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)
    # mock out the rabbit connection
    job_queue.rabbitmq = MockRabbit()

    storage = MockDataStorage()

    generator = WorkGenerator(job_queue, api, storage)
    generator.download('documents')

    assert job_queue.get_num_jobs() == 150


def test_work_generator_large(requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(6666).get_results()
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)
    # mock out the rabbit connection
    job_queue.rabbitmq = MockRabbit()

    storage = MockDataStorage()
    generator = WorkGenerator(job_queue, api, storage)
    generator.download('documents')

    assert job_queue.get_num_jobs() == 6666


def test_work_generator_retries_after_500(requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(150).get_results()
    results.insert(0, {'json': '{}', 'status_code': 500})
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)
    # mock out the rabbit connection
    job_queue.rabbitmq = MockRabbit()

    storage = MockDataStorage()
    generator = WorkGenerator(job_queue, api, storage)
    generator.download('documents')

    assert len(requests_mock.request_history) == 2


def test_work_generator_catches_job_queue_exception(requests_mock, mocker):
    """
    Test that the Work Generator has proper handling when encountering a
    JobQueueException (currently using RabbitMQ: RabbitMQ Exception as result
    of losing connection to a Channel raises JobQueueException.
    """
    results = MockDataSet(10).get_results()
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)
    # mock out the rabbit connection
    job_queue.rabbitmq = MockRabbit()

    # mock the job queue to raise a JobQueueException when a job is added.
    # Essentially replaces the original add_job method of the job_queue object
    # with a new method that raises the JobQueueException exception
    mocker.patch.object(job_queue, 'add_job', side_effect=JobQueueException())

    storage = MockDataStorage()

    generator = WorkGenerator(job_queue, api, storage)

    # Attempt to generate work and ensure that a JobQueueException is raised
    with pytest.raises(JobQueueException):
        generator.download('documents')


def test_work_generator_output_after_500_error(capsys, requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(150).get_results()
    results.insert(0, {'json': '{}', 'status_code': 504})
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(FakeRedis())
    # mock out the rabbit connection
    job_queue.rabbitmq = MockRabbit()

    generator = WorkGenerator(job_queue, api, MockDataStorage())
    generator.download('documents')

    print_data = [
        'FAILED: https://api.regulations.gov/v4/documents\n',
        '504 Server Error: None for url: ',
        'https://api.regulations.gov/v4/documents?',
        'sort=lastModifiedDate&page[size]=250',
        '&filter[lastModifiedDate][ge]=1971-12-31+19:00:00&page[number]=1\n',
        'Added any: 150\n'
    ]
    assert capsys.readouterr().out == "".join(print_data)
