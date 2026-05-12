"""Tests for mirrclient.logutil."""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from mirrclient.logutil import (
    configure_client_logging,
    entity_from_job_url,
    kind_singular,
    redact_url,
)


@pytest.mark.parametrize(
    ('url', 'want'),
    [
        ('', ''),
        (
            'https://api.regulations.gov/v4/dockets/ABC-123',
            'https://api.regulations.gov/v4/dockets/ABC-123',
        ),
        (
            'https://api.regulations.gov/v4/comments/XYZ?page=2&api_key=secret',
            'https://api.regulations.gov/v4/comments/XYZ?page=2',
        ),
        (
            'http://localhost/job?ApiKey=hunter2&keep=1',
            'http://localhost/job?keep=1',
        ),
        (
            'https://example.com/path?foo=1&APIKEY=x&bar=2',
            'https://example.com/path?foo=1&bar=2',
        ),
        (
            'https://example.com/path?foo=bar#frag',
            'https://example.com/path?foo=bar#frag',
        ),
    ],
)
def test_redact_url(url, want):
    assert redact_url(url) == want


@pytest.mark.parametrize(
    ('url', 'want'),
    [
        ('', ''),
        (
            'https://api.regulations.gov/v4/dockets/USTR-2015-0010',
            'USTR-2015-0010',
        ),
        (
            'https://api.regulations.gov/v4/documents/USTR-2015-0010-0001/?extra=1',
            'USTR-2015-0010-0001',
        ),
        (
            'https://example.com/comments/ABC-001-002/',
            'ABC-001-002',
        ),
    ],
)
def test_entity_from_job_url(url, want):
    assert entity_from_job_url(url) == want


@pytest.mark.parametrize(
    ('job_type', 'want'),
    [
        ('dockets', 'docket'),
        ('documents', 'document'),
        ('comments', 'comment'),
        ('widgets', 'widgets'),
        ('', 'other'),
    ],
)
def test_kind_singular(job_type, want):
    assert kind_singular(job_type) == want


@patch('mirrclient.logutil.logging.getLogger')
def test_configure_client_logging_sets_level_and_adds_handler(mock_get_logger):
    """Root is isolated: pytest's LogCaptureHandler would make this a no-op."""
    mock_root = MagicMock()
    mock_root.handlers = []
    mock_get_logger.return_value = mock_root

    with patch.dict('os.environ', {'LOG_LEVEL': 'WARNING'}, clear=False):
        configure_client_logging()

    mock_root.setLevel.assert_called_once_with(logging.WARNING)
    mock_root.addHandler.assert_called_once()
    handler = mock_root.addHandler.call_args[0][0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.formatter.converter is time.gmtime


@patch('mirrclient.logutil.logging.getLogger')
def test_configure_client_logging_idempotent(mock_get_logger):
    class _FakeRoot:
        """Minimal root logger stand-in (mirrors logging.Logger names)."""

        def __init__(self):
            self.handlers = []
            self.level = logging.NOTSET

        def addHandler(self, handler):  # pylint: disable=invalid-name
            self.handlers.append(handler)

        def setLevel(self, level):  # pylint: disable=invalid-name
            self.level = level

    fake_root = _FakeRoot()
    mock_get_logger.return_value = fake_root

    with patch.dict('os.environ', {'LOG_LEVEL': 'ERROR'}, clear=False):
        configure_client_logging()
        configure_client_logging()

    assert len(fake_root.handlers) == 1
    assert fake_root.level == logging.ERROR


@patch('mirrclient.logutil.logging.getLogger')
def test_configure_client_logging_unknown_level_defaults_to_info(mock_get_logger):
    mock_root = MagicMock()
    mock_root.handlers = []
    mock_get_logger.return_value = mock_root

    with patch.dict('os.environ', {'LOG_LEVEL': 'NOT_A_REAL_LEVEL'}, clear=False):
        configure_client_logging()

    mock_root.setLevel.assert_called_once_with(logging.INFO)


@patch('mirrclient.logutil.logging.getLogger')
def test_configure_client_logging_debug_level(mock_get_logger):
    mock_root = MagicMock()
    mock_root.handlers = []
    mock_get_logger.return_value = mock_root

    with patch.dict('os.environ', {'LOG_LEVEL': 'DEBUG'}, clear=False):
        configure_client_logging()

    mock_root.setLevel.assert_called_once_with(logging.DEBUG)
