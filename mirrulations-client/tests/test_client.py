# pylint: disable=W0212
import os
import responses
from pytest import fixture
import pytest
import requests_mock
from requests.exceptions import ReadTimeout
import boto3
from mirrcore.path_generator import PathGenerator
from mirrclient.client import Client, is_environment_variables_present
from mirrclient.exceptions import NoJobsAvailableException, APITimeoutException
from mirrmock.mock_redis import ReadyRedis, InactiveRedis, MockRedisWithStorage
from mirrmock.mock_job_queue import MockJobQueue


BASE_URL = 'http://work_server:8080'


@fixture(autouse=True)
def mock_env():
    os.environ['API_KEY'] = 'TESTING_KEY'
    os.environ['ID'] = '-1'
    os.environ['AWS_ACCESS_KEY'] = 'test_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'


@fixture(name='mock_requests')
def fixture_mock_requests():
    return requests_mock.Mocker()


@fixture(name="path_generator")
def get_path():
    return PathGenerator()


@fixture(autouse=True)
def mock_disk_writing(mocker):
    """
    Mock tests that would be writing to disk
    """
    # patch _write_results and AttachmentSaver.save
    mocker.patch.object(
        Client,
        '_put_results',
        return_value=None
    )
    mocker.patch.object(
        Client,
        '_download_single_attachment',
        return_value=None
    )


def test_check_no_env_values():
    # Need to delete env variables set by mock_env fixture
    del os.environ['API_KEY']
    assert is_environment_variables_present() is False


def test_check_no_api_key():
    # Need to delete api key env variable set by mock_env fixture
    del os.environ['API_KEY']
    assert is_environment_variables_present() is False


def test_client_has_no_id():
    # Need to delete id env variable set by mock_env fixture
    del os.environ['ID']
    assert is_environment_variables_present() is False


def create_mock_mirrulations_bucket():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="mirrulations")
    return conn


def test_set_missing_job_key_defaults():
    client = Client(ReadyRedis(), MockJobQueue())
    job = {
        'job_id': 1,
        'url': 'regulations.gov',
        'job_type': 'comments'
    }
    job = client._set_missing_job_key_defaults(job)
    final_job = {
        'job_id': 1,
        'url': 'regulations.gov',
        'job_type': 'comments',
        'reg_id': 'other_reg_id',
        'agency': 'other_agency'
    }
    assert job == final_job


def test_remove_plural_from_job():
    client = Client(ReadyRedis(), MockJobQueue())
    job = {'url': 'regulations.gov/comments/DOD-0001-0001'}
    job_without_plural = client._remove_plural_from_job_type(job)
    assert job_without_plural == 'comment/DOD-0001-0001'


def test_can_connect_to_database():
    client = Client(ReadyRedis(), MockJobQueue())
    assert client._can_connect_to_database()


def test_api_call_has_api_key(mock_requests):
    client = Client(MockRedisWithStorage(), MockJobQueue())
    client.api_key = 'KEY12345'
    with mock_requests:
        mock_requests.get(
            'http://regulations.gov/job',
            json={'data': {'foo': 'bar'}},
            status_code=200
        )
        client._perform_job('http://regulations.gov/job')


def test_cannot_connect_to_database():
    client = Client(InactiveRedis(), MockJobQueue())
    assert not client._can_connect_to_database()


def test_job_queue_is_empty():
    client = Client(ReadyRedis(), MockJobQueue())
    with pytest.raises(NoJobsAvailableException):
        client.job_operation()


def test_get_job_from_job_queue_no_redis():
    client = Client(InactiveRedis(), MockJobQueue())
    with pytest.raises(NoJobsAvailableException):
        client._get_job_from_job_queue()


def test_get_job_from_job_queue_gets_job():
    client = Client(ReadyRedis(), MockJobQueue())
    client.job_queue = MockJobQueue()
    client.job_queue.add_job({'job': 'This is a job'})
    assert client._get_job_from_job_queue() == {'job': 'This is a job'}


def test_get_job():
    client = Client(ReadyRedis(), MockJobQueue())
    client.job_queue = MockJobQueue()
    job = {
        'job_id': 1,
        'url': 'https://api.regulations.gov/v4/dockets/type_id',
        'job_type': 'comments',
        'reg_id': 'other_reg_id',
        'agency': 'other_agency'
    }
    client.job_queue.add_job(job)
    assert client._get_job() == job


def test_client_hsets_redis_values():
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue())
    mock_redis.set('jobs_in_progress', ['foo', 'var'])
    mock_redis.set('client_jobs', ['foo', 'bar'])
    job = {'job_id': 1,
           'url': 'fake.com'}
    client._set_redis_values(job)
    assert mock_redis.get('jobs_in_progress') == [1, 'fake.com']
    assert mock_redis.get('client_jobs') == [1, '-1']


# Document HTM Tests
def test_document_has_file_formats_does_not_have_data():
    client = Client(ReadyRedis(), MockJobQueue())
    json = {}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_does_not_have_attributes():
    client = Client(ReadyRedis(), MockJobQueue())
    json = {'data': {}}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_where_file_formats_is_none():
    client = Client(ReadyRedis(), MockJobQueue())
    json = {'data': {"attributes": {"fileFormats": None}}}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_does_not_have_file_formats():
    client = Client(ReadyRedis(), MockJobQueue())
    json = {'data': {'attributes': []}}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_has_required_fields():
    client = Client(ReadyRedis(), MockJobQueue())
    json = {'data': {'attributes': {'fileFormats': {}}}}
    assert client._document_has_file_formats(json)


def test_get_document_htm_returns_link():
    client = Client(ReadyRedis(), MockJobQueue())
    json = {'data': {
                'attributes': {
                    'fileFormats': [{
                        'format': 'htm',
                        'fileUrl': 'fake.com'}]}}}
    assert client._get_document_htm(json) == 'fake.com'


def test_get_document_htm_returns_none():
    client = Client(ReadyRedis(), MockJobQueue())
    json = {'data': {
                'attributes': {
                    'fileFormats': [{
                        'format': 'pdf',
                        'fileUrl': 'fake.pdf'}]}}}
    assert client._get_document_htm(json) is None


@responses.activate
def test_client_downloads_document_htm(capsys, mocker):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    mocker.patch('mirrclient.s3_saver.S3Saver.save_binary',
                 return_value=None)
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue())
    client.api_key = 1234
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/documents',
                              "job_type": "documents"})
    mock_redis.set('jobs_in_progress', [1, 'http://regulations.gov/documents'])

    test_json = {'data': {'id': '1', 'type': 'documents',
                                'attributes':
                                {'agencyId': 'USTR',
                                 'docketId': 'USTR-2015-0010',
                                    "fileFormats": [{
                                        "fileUrl":
                                            ("http://downloads.regulations."
                                                "gov/USTR-2015-0010-0001/"
                                             "content.htm"),
                                        "format": "htm",
                                        "size": 9709
                                    }]},
                                'job_type': 'documents'}}
    responses.add(responses.GET, 'http://regulations.gov/documents',
                  json=test_json, status=200)
    responses.add(responses.GET,
                  'http://downloads.regulations.gov/' +
                  'USTR-2015-0010-0001/content.htm',
                  json='\bx17', status=200)
    client.job_operation()
    captured = capsys.readouterr()
    print_data = [
        'Processing job from RabbitMQ.\n',
        'Attempting to get job\n',
        'Job received from job queue\n',
        'Job received: documents for client: -1\n',
        'Regulations.gov link: http://regulations.gov/documents\n',
        'API URL: http://regulations.gov/documents\n',
        'Performing job.\n',
        'Downloading Job 1\n',
        ('SAVED document HTM '
            '- http://downloads.regulations.gov/USTR-2015-0010-0001/'
            'content.htm to path:  '
            '/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/'
            '1_content.htm\n')
    ]
    assert captured.out == "".join(print_data)


# Client Comment Attachments
def test_does_comment_have_attachment_has_attachment():
    client = Client(ReadyRedis(), MockJobQueue())
    comment_json = {'included': [0]}
    assert client._does_comment_have_attachment(comment_json)


def test_does_comment_have_attachment_does_have_attachment():
    client = Client(ReadyRedis(), MockJobQueue())
    comment_json = {'included': []}
    assert not client._does_comment_have_attachment(comment_json)


@responses.activate
def test_handles_none_in_comment_file_formats(path_generator):
    """
    Test for handling of the NoneType Error caused by null fileformats
    """
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue())
    client.api_key = 1234
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/job',
                              "job_type": "comments"})
    mock_redis.set('jobs_in_progress', [1,
                                        'http://regulations.gov/job'])
    test_json = {
                "data": {
                    "id": "agencyID-001-0002",
                    "type": "comments",
                    "attributes": {
                        "agencyId": "agencyID",
                        "docketId": "agencyID-001"
                    }
                },
                "included": [{
                    "attributes": {
                        "fileFormats": None
                    },
                }]}
    responses.add(responses.GET, 'http://regulations.gov/job',
                  json=test_json, status=200)
    client.job_operation()
    assert mock_redis.get('jobs_in_progress') == [1,
                                                  'http://regulations.gov/job']
    assert mock_redis.get('client_jobs') == [1, '-1']

    attachment_paths = path_generator.get_attachment_json_paths(test_json)
    assert attachment_paths == []


@responses.activate
def test_client_downloads_attachment_results(mocker, capsys):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue())
    client.api_key = 1234
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/comments',
                              "job_type": "comments"})
    mock_redis.set('jobs_in_progress', [1, 'http://regulations.gov/comments'])

    test_json = {
                "data": {
                    "id": "FDA-2016-D-2335-1566",
                    "type": "comments",
                    "attributes": {
                        "agencyId": "FDA",
                        "docketId": "FDA-2016-D-2335"
                    }
                },
                "included": [{
                    "attributes": {
                        "fileFormats": [{
                                 "fileUrl": ("http://downloads.regulations."
                                             "gov/FDA-2016-D-2335/"
                                             "attachment_1.pdf")
                        }]
                    }
                }]
            }
    responses.add(responses.GET, 'http://regulations.gov/comments',
                  json=test_json, status=200)
    responses.add(responses.GET,
                  ('http://downloads.regulations.gov/\
                   FDA-2016-D-2335/attachment_1.pdf'),
                  json='\bx17', status=200)

    client.job_operation()
    job_stat_results = client.cache.get_jobs_done()
    assert job_stat_results['num_comments_done'] == 1
    assert job_stat_results['num_attachments_done'] == 1
    assert job_stat_results['num_pdf_attachments_done'] == 1

    captured = capsys.readouterr()
    print_data = [
        'Processing job from RabbitMQ.\n',
        'Attempting to get job\n',
        'Job received from job queue\n',
        'Job received: comments for client: -1\n',
        'Regulations.gov link: http://regulations.gov/comments\n',
        'API URL: http://regulations.gov/comments\n',
        'Performing job.\n',
        'Downloading Job 1\n',
        'Found 1 attachment(s) for Comment - FDA-2016-D-2335-1566\n',
        'Downloaded 1/1 attachment(s) for Comment - FDA-2016-D-2335-1566\n'
    ]
    assert captured.out == "".join(print_data)


@responses.activate
def test_does_comment_have_attachment_with_empty_attachment_list():
    """
    Test that handles empty attachment list from comments json being:
    {
        "relationships" : {
                "attachments" : {
                    "data" : [ ]}
                    }
    }
    """
    client = Client(ReadyRedis(), MockJobQueue())
    client.api_key = 1234

    test_json = {
                "data": {
                    "id": "agencyID-001-0002",
                    "type": "comments",
                    "attributes": {
                        "agencyId": "agencyID",
                        "docketId": "agencyID-001"
                    }
                },
                "relationships": {
                    "attachments": {
                        "data": []
                    }
                }
            }
    assert client._does_comment_have_attachment(test_json) is False


@responses.activate
def test_two_attachments_in_comment(mocker):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    client = Client(ReadyRedis(), MockJobQueue())
    client.api_key = 1234

    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/job',
                              "job_type": "comments"})

    test_json = {
            "data": {
                "id": "agencyID-001-0002",
                "type": "comments",
                "attributes": {
                    "agencyId": "agencyID",
                    "docketId": "agencyID-001"
                }
            },
            "included": [{
                "attributes": {
                    "fileFormats": [{
                        "fileUrl": "https://downloads.regulations.gov/.pdf"
                    }, {
                        "fileUrl": "https://downloads.regulations.gov/.doc"
                    }]
                }
            }]
        }
    responses.add(responses.GET, 'http://regulations.gov/job',
                  json=test_json, status=200)

    client.job_operation()
    results = client.cache.get_jobs_done()
    assert results['num_comments_done'] == 1
    assert results['num_attachments_done'] == 2
    assert results['num_pdf_attachments_done'] == 1


# Exception Tests
def test_get_job_is_empty():
    client = Client(ReadyRedis(), MockJobQueue())
    with pytest.raises(NoJobsAvailableException):
        client._get_job()


def test_client_perform_job_times_out(mock_requests):
    with mock_requests:
        fake_url = 'http://regulations.gov/fake/api/call'
        mock_requests.get(
            fake_url,
            exc=ReadTimeout)

        with pytest.raises(APITimeoutException):
            client = Client(MockRedisWithStorage(), MockJobQueue())
            client._perform_job(fake_url)


@responses.activate
def test_client_handles_api_timeout():
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue())
    client.api_key = 1234
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/job',
                              "job_type": "comments"})
    mock_redis.set('jobs_in_progress', [1, 'http://regulations.gov/job'])

    responses.get("http://regulations.gov/job",
                  body=ReadTimeout("Read Timeout"))

    with pytest.raises(APITimeoutException):
        client.job_operation()

    assert mock_redis.get('invalid_jobs') == [1, 'http://regulations.gov/job']
