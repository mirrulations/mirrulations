"""Focused tests for client helpers (no autouse disk mocks from test_client)."""

import logging
# pylint: disable=protected-access
from unittest.mock import MagicMock

import pytest
import requests

from mirrclient.client import Client
from mirrclient.key_manager import KeyManager
from mirrmock.mock_job_queue import MockJobQueue
from mirrmock.mock_redis import ReadyRedis


@pytest.fixture(name='key_manager')
def fixture_key_manager(tmp_client_keys_path):
    return KeyManager(str(tmp_client_keys_path))


def test_put_results_calls_saver_save_json(key_manager, mocker):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    mock_save = mocker.patch.object(client.saver, 'save_json')
    data = {
        'directory': '/agency/docket/text-x/comments/C-1.json',
        'job_type': 'comments',
        'results': {'data': {'id': 'C-1'}},
    }
    client._put_results(data)
    mock_save.assert_called_once_with(
        '/data/agency/docket/text-x/comments/C-1.json',
        data,
    )


def test_download_single_attachment_fetches_and_writes(key_manager, mocker):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    mock_get = mocker.patch(
        'mirrclient.client.requests.get',
        return_value=MagicMock(content=b'body'),
    )
    mock_bin = mocker.patch.object(client.saver, 'save_binary')
    attach_path = '/raw-data/A/D/binary-D/attachments/f.pdf'
    client._download_single_attachment('https://example.com/f.pdf', attach_path)
    mock_get.assert_called_once_with('https://example.com/f.pdf', timeout=10)
    mock_bin.assert_called_once_with(
        '/data/raw-data/A/D/binary-D/attachments/f.pdf',
        b'body',
    )


def test_download_htm_skips_fetch_when_url_none(key_manager, mocker):
    """Early return when no downloadable URL (defensive guard)."""
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    mocker.patch.object(client, '_get_document_htm', return_value=None)
    mock_save = mocker.patch.object(client.saver, 'save_binary')
    doc = {
        'data': {
            'id': 'USTR-2015-0010-0001',
            'attributes': {
                'fileFormats': [
                    {'format': 'htm', 'fileUrl': None},
                ],
            },
        },
    }
    client._download_htm(doc, 'testkey')
    mock_save.assert_not_called()


def test_job_operation_logs_request_exception(caplog, key_manager, mocker):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    client.job_queue.add_job({
        'job_id': 1,
        'url': 'http://regulations.gov/dockets/X',
        'job_type': 'dockets',
    })
    mocker.patch(
        'mirrclient.client.requests.get',
        side_effect=requests.ConnectionError('unavailable'),
    )
    with caplog.at_level(logging.ERROR, logger='mirrclient.client'):
        with pytest.raises(requests.ConnectionError):
            client.job_operation(key_manager.get_next())
    messages = ' '.join(r.message for r in caplog.records)
    assert 'job failed' in messages
    assert 'unavailable' in messages


def test_job_operation_logs_valueerror_on_bad_json(caplog, key_manager, mocker):
    client = Client(ReadyRedis(), MockJobQueue(), key_manager)
    client.job_queue.add_job({
        'job_id': 1,
        'url': 'http://regulations.gov/dockets/X',
        'job_type': 'dockets',
    })
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.side_effect = ValueError('not json')
    mocker.patch.object(client, '_perform_job', return_value=response)
    with caplog.at_level(logging.ERROR, logger='mirrclient.client'):
        with pytest.raises(ValueError):
            client.job_operation(key_manager.get_next())
    messages = ' '.join(r.message for r in caplog.records)
    assert 'invalid_response' in messages
