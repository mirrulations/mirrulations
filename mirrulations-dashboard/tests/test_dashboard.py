from collections import namedtuple
from unittest.mock import Mock, MagicMock
from pytest import fixture

from mirrcore.job_queue import JobQueue
from mirrdash.dashboard_server import create_server, \
    get_container_stats, get_container_name
from fakeredis import FakeRedis, FakeServer
from mirrmock.mock_data_storage import MockDataStorage
from mirrmock.mock_document_count import create_mock_mongodb
from mirrmock.mock_rabbitmq import MockRabbit


@fixture(name='mock_server')
def fixture_mock_server():
    redis_server = FakeServer()
    mock_redis_db = FakeRedis(server=redis_server)
    mock_docker = MagicMock()
    mock_mongo_db = create_mock_mongodb(1, 2, 3, 4)
    job_queue = JobQueue(mock_redis_db)
    job_queue.rabbitmq = MockRabbit()
    server = create_server(job_queue,
                           mock_docker, mock_mongo_db)
    server.redis_server = redis_server
    server.app.config['TESTING'] = True
    server.client = server.app.test_client()
    server.data = MockDataStorage()
    return server


def add_mock_data_to_database(job_queue):
    for job in range(1, 6):
        job_queue.add_job(f'http://requlations.gov/job{job}')
    jobs_in_progress = {i: i for i in range(6, 10)}
    # Reach into the Redis DB and set some values.  UGH
    job_queue.database.hset('jobs_in_progress', mapping=jobs_in_progress)
    jobs_done = {i: i for i in range(10, 13)}
    job_queue.database.hset('jobs_done', mapping=jobs_done)
    job_queue.database.set('total_num_client_ids', 2)
    job_queue.database.set('num_jobs_comments_waiting', 2)
    job_queue.database.set('num_jobs_documents_waiting', 2)
    job_queue.database.set('num_jobs_dockets_waiting', 1)


def test_dashboard_returns_job_information(mock_server):
    client = MagicMock()

    # Mock out the docker object to return Container-like values
    # for the list method.
    Container = namedtuple('Container', ['name', 'status'])
    return_value = [Container('capstone_client1_1', 'running'),
                    Container('capstone_work_server_1', 'running')]
    client.containers.list = Mock(return_value=return_value)

    add_mock_data_to_database(mock_server.job_queue)
    mock_server.docker = client
    response = mock_server.client.get('/data')

    assert response.status_code == 200
    results = response.get_json()
    assert results['num_jobs_waiting'] == 5
    assert results['num_jobs_in_progress'] == 4
    assert results['num_jobs_done'] == 10
    assert results['jobs_total'] == 19
    assert results['num_jobs_comments_queued'] == 2
    assert results['num_jobs_documents_queued'] == 2
    assert results['num_jobs_dockets_queued'] == 1


def test_dashboard_returns_html(mock_server):
    add_mock_data_to_database(mock_server.job_queue)
    response = mock_server.client.get('/')

    assert response.status_code == 200
    expected = '<!DOCTYPE html>'
    assert response.data.decode().split('\n')[0] == expected


def test_get_container_stats():
    client = MagicMock()

    # Mock out the docker object to return Container-like values
    # for the list method.
    Container = namedtuple('Container', ['name', 'status'])
    return_value = [Container('capstone_client1_1', 'running'),
                    Container('capstone_work_server_1', 'running')]
    client.containers.list = Mock(return_value=return_value)

    stats = get_container_stats(client)

    expected = {'client1': 'running',
                'work_server': 'running'}

    assert stats == expected


def test_docker_name_formatted():
    name = '_capstone2022-work_generator-1_'
    assert get_container_name(name) == 'capstone2022_work_generator_1'
