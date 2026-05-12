"""Shared pytest fixtures for mirrulations-client."""

import pytest

TEST_API_KEY = 'TESTINGKEY123'


@pytest.fixture
def tmp_client_keys_path(tmp_path, monkeypatch):
    """Write a minimal client_keys.json and set CLIENT_KEYS_PATH."""
    keys_path = tmp_path / 'client_keys.json'
    keys_path.write_text(
        f'[{{"id":"testkey","api_key":"{TEST_API_KEY}"}}]',
        encoding='utf-8')
    monkeypatch.setenv('CLIENT_KEYS_PATH', str(keys_path))
    return keys_path
