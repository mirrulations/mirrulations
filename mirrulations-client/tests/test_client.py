# pylint: disable=W0212
import logging
import os
from unittest.mock import MagicMock

import boto3
import pytest
import requests_mock
import responses
from pytest import fixture
from requests.exceptions import ReadTimeout
from mirrcore.comment_attachments import comment_attachment_file_format_count
from mirrcore.path_generator import PathGenerator
from mirrclient.client import Client, _build_savers, \
    is_client_keys_path_configured
from mirrclient.disk_saver import DiskSaver
from mirrclient.s3_saver import S3Saver
from mirrclient.exceptions import RedisPingFailedError, APITimeoutException
from mirrclient.key_manager import KeyManager
from mirrmock.mock_redis import ReadyRedis, InactiveRedis, MockRedisWithStorage
from mirrmock.mock_job_queue import MockJobQueue
from mirrmock.regulations_api_fixtures import (
    get_test_comment,
    get_test_docket,
    get_test_document,
)


TEST_API_KEY = 'TESTINGKEY123'
TEST_KEY_QUERY = f'?api_key={TEST_API_KEY}'


@fixture(autouse=True)
def mock_env(tmp_client_keys_path, monkeypatch):  # pylint: disable=unused-argument
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
    ok_download = MagicMock(ok=True, status_code=200, content=b'')
    mocker.patch.object(
        Client,
        '_put_results',
        return_value=None
    )
    mocker.patch.object(
        Client,
        '_download_single_attachment',
        return_value=ok_download
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
    assert client.job_operation(key_manager.get_next()) is None


def test_get_job_from_job_queue_no_redis(key_manager):
    client = Client(InactiveRedis(), MockJobQueue(), key_manager)
    with pytest.raises(RedisPingFailedError):
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
def test_client_downloads_document_htm(caplog, mocker, key_manager):
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
    with caplog.at_level(logging.DEBUG, logger='mirrclient.client'):
        client.job_operation(key_manager.get_next())
    messages = ' '.join(r.message for r in caplog.records)
    assert 'wrote artifact kind=document type=htm' in messages


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
def test_handles_none_in_comment_file_formats(key_manager):
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

    assert comment_attachment_file_format_count(test_json) == 0


@responses.activate
# pylint: disable=too-many-locals
def test_client_downloads_attachment_results(mocker, caplog, key_manager):
    mocker.patch('mirrclient.disk_saver.DiskSaver.make_path',
                 return_value=None)
    mocker.patch('mirrclient.disk_saver.DiskSaver.save_binary',
                 return_value=None)
    mocker.patch('mirrclient.s3_saver.S3Saver.save_binary',
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

    with caplog.at_level(logging.DEBUG, logger='mirrclient.client'):
        client.job_operation(key_manager.get_next())
    job_stat_results = client.cache.get_jobs_done()
    assert job_stat_results['num_comments_done'] == 1
    assert job_stat_results['num_attachments_done'] == 1
    assert job_stat_results['num_pdf_attachments_done'] == 1

    messages = ' '.join(r.message for r in caplog.records)
    assert 'Comment attachments scheduled' in messages
    assert 'wrote artifact kind=attachment' in messages


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
    mocker.patch('mirrclient.s3_saver.S3Saver.save_binary',
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
    assert client._get_job('testkey') is None


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
def test_client_handles_api_timeout(caplog, key_manager):
    mock_redis = ReadyRedis()
    client = Client(mock_redis, MockJobQueue(), key_manager)
    client.job_queue.add_job({'job_id': 1,
                              'url': 'http://regulations.gov/job',
                              "job_type": "comments"})

    responses.get(f"http://regulations.gov/job{TEST_KEY_QUERY}",
                  body=ReadTimeout("Read Timeout"))

    with caplog.at_level(logging.ERROR, logger='mirrclient.client'):
        with pytest.raises(APITimeoutException):
            client.job_operation(key_manager.get_next())

    assert 'reason=timeout' in caplog.text
    assert 'http://regulations.gov/job' in caplog.text
    assert 'job_id' not in caplog.text


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
def test_client_downloads_document_html(caplog, mocker, key_manager):
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
    with caplog.at_level(logging.DEBUG, logger='mirrclient.client'):
        client.job_operation(key_manager.get_next())
    messages = ' '.join(r.message for r in caplog.records)
    assert 'wrote artifact kind=document type=html' in messages


def test_primary_json_corpus_path_docket(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    job_result = get_test_docket()
    assert client._primary_json_corpus_path(job_result) == (
        '/raw-data/USTR/USTR-2015-0010/text-USTR-2015-0010/docket/USTR-2015-0010.json'
    )


def test_primary_json_corpus_path_comment_and_document(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    comment = get_test_comment()
    assert client._primary_json_corpus_path(comment) == (
        '/raw-data/USTR/USTR-2015-0010/text-USTR-2015-0010/comments/'
        'USTR-2015-0010-0002.json'
    )
    document = get_test_document()
    assert client._primary_json_corpus_path(document) == (
        '/raw-data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/'
        'USTR-2015-0010-0015.json'
    )


def test_primary_json_corpus_path_missing_or_invalid_payload(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    assert client._primary_json_corpus_path({}) == '/unknown/unknown.json'
    assert client._primary_json_corpus_path({'data': []}) == (
        '/unknown/unknown.json'
    )
    assert client._primary_json_corpus_path({'data': {'type': -1}}) == (
        '/unknown/unknown.json'
    )


def test_primary_json_corpus_path_unknown_type(key_manager):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    unknown = {'data': {'type': 'unknown'}}
    assert client._primary_json_corpus_path(unknown) == (
        '/raw-data/unknown/unknown.json'
    )


def test_build_savers_default_bucket_when_unset(monkeypatch):
    monkeypatch.delenv('S3_BUCKET', raising=False)
    savers = _build_savers()
    assert len(savers) == 2
    assert isinstance(savers[0], DiskSaver)
    assert isinstance(savers[1], S3Saver)
    assert savers[1].bucket_name == 'mirrulations'


def test_build_savers_custom_bucket(monkeypatch):
    monkeypatch.setenv('S3_BUCKET', 'my-custom-bucket')
    savers = _build_savers()
    assert len(savers) == 2
    assert savers[1].bucket_name == 'my-custom-bucket'


def test_build_savers_empty_env_disables_s3(monkeypatch):
    monkeypatch.setenv('S3_BUCKET', '')
    savers = _build_savers()
    assert len(savers) == 1
    assert isinstance(savers[0], DiskSaver)


def test_build_savers_whitespace_only_disables_s3(monkeypatch):
    monkeypatch.setenv('S3_BUCKET', '   ')
    savers = _build_savers()
    assert len(savers) == 1
