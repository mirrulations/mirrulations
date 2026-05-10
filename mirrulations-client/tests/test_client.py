# pylint: disable=W0212
import os
import responses
from pytest import fixture
import pytest
import requests_mock
from requests.exceptions import ReadTimeout
import boto3
from mirrcore.path_generator import PathGenerator
from mirrclient.client import Client, is_client_keys_path_configured
from mirrclient.exceptions import NoJobsAvailableException, APITimeoutException
from mirrclient.key_manager import KeyManager
from mirrmock.mock_redis import ReadyRedis, InactiveRedis, MockRedisWithStorage
from mirrmock.mock_job_queue import MockJobQueue


TEST_API_KEY = 'TESTINGKEY123'
TEST_KEY_QUERY = f'?api_key={TEST_API_KEY}'


@fixture(autouse=True)
def mock_env(tmp_path, monkeypatch):
    keys_path = tmp_path / 'client_keys.json'
    keys_path.write_text(
        f'[{{"id":"testkey","api_key":"{TEST_API_KEY}"}}]',
        encoding='utf-8')
    monkeypatch.setenv('CLIENT_KEYS_PATH', str(keys_path))
    monkeypatch.setenv('AWS_ACCESS_KEY', 'test_key')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test_secret_key')


@fixture(name='key_manager')
def fixture_key_manager():
    return KeyManager(os.environ['CLIENT_KEYS_PATH'])


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


def test_no_client_keys_path(monkeypatch):
    monkeypatch.delenv('CLIENT_KEYS_PATH', raising=False)
    assert is_client_keys_path_configured() is False


def test_client_keys_path_configured():
    assert is_client_keys_path_configured() is True


def create_mock_mirrulations_bucket():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="mirrulations")
    return conn


def test_set_missing_job_key_defaults(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
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


def test_remove_plural_from_job(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    job = {'url': 'regulations.gov/comments/DOD-0001-0001'}
    job_without_plural = client._remove_plural_from_job_type(job)
    assert job_without_plural == 'comment/DOD-0001-0001'


def test_can_connect_to_database(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    assert client._can_connect_to_database()


def test_api_call_has_api_key(mock_requests, key_manager):
    client = Client(MockRedisWithStorage(), MockJobQueue(), key_manager)
    credential = key_manager.get_next()
    with mock_requests:
        mock_requests.get(
            f'http://regulations.gov/job{TEST_KEY_QUERY}',
            json={'data': {'foo': 'bar'}},
            status_code=200
        )
        client._perform_job('http://regulations.gov/job', credential)


def test_cannot_connect_to_database(key_manager):
    client = Client(InactiveRedis(), MockJobQueue(), key_manager)
    assert not client._can_connect_to_database()


def test_job_queue_is_empty(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    with pytest.raises(NoJobsAvailableException):
        client.job_operation(key_manager.get_next())


def test_get_job_from_job_queue_no_redis(key_manager):
    client = Client(InactiveRedis(), MockJobQueue(), key_manager)
    with pytest.raises(NoJobsAvailableException):
        client._get_job_from_job_queue()


def test_get_job_from_job_queue_gets_job(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    client.job_queue = MockJobQueue()
    client.job_queue.add_job({'job': 'This is a job'})
    assert client._get_job_from_job_queue() == {'job': 'This is a job'}


def test_get_job(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    client.job_queue = MockJobQueue()
    job = {
        'job_id': 1,
        'url': 'https://api.regulations.gov/v4/dockets/type_id',
        'job_type': 'comments',
        'reg_id': 'other_reg_id',
        'agency': 'other_agency'
    }
    client.job_queue.add_job(job)
    assert client._get_job('testkey') == job


# Document HTM Tests
def test_document_has_file_formats_does_not_have_data(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_does_not_have_attributes(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {}}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_where_file_formats_is_none(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {"attributes": {"fileFormats": None}}}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_does_not_have_file_formats(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {'attributes': []}}
    assert not client._document_has_file_formats(json)


def test_document_has_file_formats_has_required_fields(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {'attributes': {'fileFormats': {}}}}
    assert client._document_has_file_formats(json)


def test_get_document_htm_returns_link(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {
                'attributes': {
                    'fileFormats': [{
                        'format': 'htm',
                        'fileUrl': 'fake.com'}]}}}
    assert client._get_document_htm(json) == 'fake.com'


def test_get_document_htm_returns_none(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {
                'attributes': {
                    'fileFormats': [{
                        'format': 'pdf',
                        'fileUrl': 'fake.pdf'}]}}}
    assert client._get_document_htm(json) is None


@responses.activate
def test_client_downloads_document_htm(capsys, mocker, key_manager):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    mocker.patch('mirrclient.s3_saver.S3Saver.save_binary',
                 return_value=None)
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue(), key_manager)
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/documents',
                              "job_type": "documents"})

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
    responses.add(responses.GET,
                  f'http://regulations.gov/documents{TEST_KEY_QUERY}',
                  json=test_json, status=200)
    responses.add(responses.GET,
                  'http://downloads.regulations.gov/' +
                  'USTR-2015-0010-0001/content.htm',
                  json='\bx17', status=200)
    client.job_operation(key_manager.get_next())
    captured = capsys.readouterr()
    print_data = [
        'Processing job from RabbitMQ.\n',
        'Attempting to get job\n',
        'Job received from job queue\n',
        'Job received: documents (api key id: testkey)\n',
        'Regulations.gov link: http://regulations.gov/documents\n',
        'API URL: http://regulations.gov/documents\n',
        'Performing job.\n',
        'Downloading Job 1\n',
        ('SAVED document HTM '
            '- http://downloads.regulations.gov/USTR-2015-0010-0001/'
            'content.htm to path:  '
            '/raw-data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/'
            '1_content.htm\n')
    ]
    assert captured.out == "".join(print_data)


# Client Comment Attachments
def test_does_comment_have_attachment_has_attachment(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    comment_json = {'included': [0]}
    assert client._does_comment_have_attachment(comment_json)


def test_does_comment_have_attachment_does_have_attachment(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    comment_json = {'included': []}
    assert not client._does_comment_have_attachment(comment_json)


@responses.activate
def test_handles_none_in_comment_file_formats(path_generator, key_manager):
    """
    Test for handling of the NoneType Error caused by null fileformats
    """
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue(), key_manager)
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
                        "fileFormats": None
                    },
                }]}
    responses.add(responses.GET,
                  f'http://regulations.gov/job{TEST_KEY_QUERY}',
                  json=test_json, status=200)
    client.job_operation(key_manager.get_next())

    attachment_paths = path_generator.get_attachment_json_paths(test_json)
    assert attachment_paths == []


@responses.activate
# pylint: disable=too-many-locals
def test_client_downloads_attachment_results(mocker, capsys, key_manager):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue(), key_manager)
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/comments',
                              "job_type": "comments"})

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
    responses.add(responses.GET,
                  f'http://regulations.gov/comments{TEST_KEY_QUERY}',
                  json=test_json, status=200)
    responses.add(responses.GET,
                  ('http://downloads.regulations.gov/\
                   FDA-2016-D-2335/attachment_1.pdf'),
                  json='\bx17', status=200)

    client.job_operation(key_manager.get_next())
    job_stat_results = client.cache.get_jobs_done()
    assert job_stat_results['num_comments_done'] == 1
    assert job_stat_results['num_attachments_done'] == 1
    assert job_stat_results['num_pdf_attachments_done'] == 1

    captured = capsys.readouterr()
    print_data = [
        'Processing job from RabbitMQ.\n',
        'Attempting to get job\n',
        'Job received from job queue\n',
        'Job received: comments (api key id: testkey)\n',
        'Regulations.gov link: http://regulations.gov/comments\n',
        'API URL: http://regulations.gov/comments\n',
        'Performing job.\n',
        'Downloading Job 1\n',
        'Found 1 attachment(s) for Comment - FDA-2016-D-2335-1566\n',
        'Downloaded 1/1 attachment(s) for Comment - FDA-2016-D-2335-1566\n'
    ]
    assert captured.out == "".join(print_data)


@responses.activate
def test_does_comment_have_attachment_with_empty_attachment_list(key_manager):
    """
    Test that handles empty attachment list from comments json being:
    {
        "relationships" : {
                "attachments" : {
                    "data" : [ ]}
                    }
    }
    """
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
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
def test_two_attachments_in_comment(mocker, key_manager):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
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
    responses.add(responses.GET,
                  f'http://regulations.gov/job{TEST_KEY_QUERY}',
                  json=test_json, status=200)

    client.job_operation(key_manager.get_next())
    results = client.cache.get_jobs_done()
    assert results['num_comments_done'] == 1
    assert results['num_attachments_done'] == 2
    assert results['num_pdf_attachments_done'] == 1


# Exception Tests
def test_get_job_is_empty(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    with pytest.raises(NoJobsAvailableException):
        client._get_job('testkey')


def test_client_perform_job_times_out(mock_requests, key_manager):
    with mock_requests:
        fake_url = 'http://regulations.gov/fake/api/call'
        mock_requests.get(
            f'{fake_url}{TEST_KEY_QUERY}',
            exc=ReadTimeout)

        with pytest.raises(APITimeoutException):
            client = Client(
                MockRedisWithStorage(), MockJobQueue(), key_manager)
            client._perform_job(fake_url, key_manager.get_next())


@responses.activate
def test_client_handles_api_timeout(capsys, key_manager):
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue(), key_manager)
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/job',
                              "job_type": "comments"})

    responses.get(f"http://regulations.gov/job{TEST_KEY_QUERY}",
                  body=ReadTimeout("Read Timeout"))

    with pytest.raises(APITimeoutException):
        client.job_operation(key_manager.get_next())

    captured = capsys.readouterr()
    assert 'job_id=1' in captured.out
    assert 'http://regulations.gov/job' in captured.out


# Document HTML Tests
def test_get_document_htm_returns_link_for_html(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {
                'attributes': {
                    'fileFormats': [{
                        'format': 'html',
                        'fileUrl': 'fake.com'}]}}}
    assert client._get_document_htm(json) == 'fake.com'


def test_get_format_returns_htm(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {'attributes': {'fileFormats': [{'format': 'htm'}]}}}
    assert client._get_format(json) == 'htm'


def test_get_format_returns_html(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    json = {'data': {'attributes': {'fileFormats': [{'format': 'html'}]}}}
    assert client._get_format(json) == 'html'


@responses.activate
def test_client_downloads_document_html(capsys, mocker, key_manager):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    mocker.patch('mirrclient.s3_saver.S3Saver.save_binary',
                 return_value=None)
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue(), key_manager)
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/documents',
                              "job_type": "documents"})

    test_json = {'data': {'id': '1', 'type': 'documents',
                                'attributes':
                                {'agencyId': 'USTR',
                                 'docketId': 'USTR-2015-0010',
                                    "fileFormats": [{
                                        "fileUrl":
                                            ("http://downloads.regulations."
                                                "gov/USTR-2015-0010-0001/"
                                             "content.html"),
                                        "format": "html",
                                        "size": 9709
                                    }]},
                                'job_type': 'documents'}}
    responses.add(responses.GET,
                  f'http://regulations.gov/documents{TEST_KEY_QUERY}',
                  json=test_json, status=200)
    responses.add(responses.GET,
                  'http://downloads.regulations.gov/' +
                  'USTR-2015-0010-0001/content.html',
                  json='\bx17', status=200)
    client.job_operation(key_manager.get_next())
    captured = capsys.readouterr()
    print_data = [
        'Processing job from RabbitMQ.\n',
        'Attempting to get job\n',
        'Job received from job queue\n',
        'Job received: documents (api key id: testkey)\n',
        'Regulations.gov link: http://regulations.gov/documents\n',
        'API URL: http://regulations.gov/documents\n',
        'Performing job.\n',
        'Downloading Job 1\n',
        ('SAVED document HTM '
            '- http://downloads.regulations.gov/USTR-2015-0010-0001/'
            'content.html to path:  '
            '/raw-data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/'
            '1_content.html\n')
    ]
    assert captured.out == "".join(print_data)
