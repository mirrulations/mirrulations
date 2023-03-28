from pytest import fixture
from mirrserver.work_server import create_server
from mirrmock.mock_flask_server import mock_work_server
from mirrcore.redis_connector import RedisConnector


@fixture(name='redis_connector')
def fixture_redis_connector():
    return RedisConnector(mock_work_server(create_server).redis)


def test_create_redis_connector(redis_connector):
    assert redis_connector.redis is not None


def test_pop_from_list_returns_none_when_list_is_empty(redis_connector):
    assert redis_connector.pop_from_list('test_list') is None


def test_pop_from_list_returns_value_when_list_is_not_empty(redis_connector):
    redis_connector.push_to_list('test_list', 'value')
    assert redis_connector.pop_from_list('test_list').decode() == 'value'


def test_push_to_list_adds_value_to_list(redis_connector):
    redis_connector.push_to_list('test_list', 'value')
    assert redis_connector.pop_from_list('test_list').decode() == 'value'


def test_add_to_hash_adds_value_to_hash(redis_connector):
    redis_connector.add_to_hash('test_hash', 'key', 'value')
    value = 'value'
    assert redis_connector.get_from_hash('test_hash', 'key').decode() == value


def test_get_from_hash_returns_none_when_hash_does_not_exist(redis_connector):
    assert redis_connector.get_from_hash('test_hash', 'key') is None


def test_get_from_hash_returns_value_when_hash_exists(redis_connector):
    redis_connector.add_to_hash('test_hash', 'key', 'value')
    value = 'value'
    assert redis_connector.get_from_hash('test_hash', 'key').decode() == value
