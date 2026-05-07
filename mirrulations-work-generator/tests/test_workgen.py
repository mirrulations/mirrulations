from fakeredis import FakeRedis
from mirrcore.job_queue import JobQueue
from mirrcore.regulations_api import RegulationsAPI
from mirrmock.mock_dataset import MockDataSet
from mirrmock.mock_rabbitmq import MockRabbit
from mirrgen.work_generator import WorkGenerator


def test_work_generator_single_page(requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(150).get_results()
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)
    # mock out the rabbit connection
    job_queue.rabbitmq = MockRabbit()

    generator = WorkGenerator(job_queue, api)
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

    generator = WorkGenerator(job_queue, api)
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

    generator = WorkGenerator(job_queue, api)
    generator.download('documents')

    assert len(requests_mock.request_history) == 2
