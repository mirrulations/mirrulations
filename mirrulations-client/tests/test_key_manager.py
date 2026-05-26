"""Scenario tests for mirrclient.key_manager.KeyManager."""

from pathlib import Path
from unittest.mock import patch

import pytest

from pydantic import ValidationError

from mirrclient.key_manager import (
    DEFAULT_CALLS_PER_HOUR_PER_KEY,
    KeyCredential,
    KeyManager,
    KeyManagerFileError,
    KeyManagerJsonError,
)


def data_file(name: str) -> Path:
    tests_dir = Path(__file__).resolve().parent
    return tests_dir / 'data' / name


def test_file_not_found(tmp_path):
    missing = tmp_path / 'no_such_keys.json'
    with pytest.raises(KeyManagerFileError) as exc:
        KeyManager(missing)
    assert 'does not exist' in str(exc.value)


def test_directory_instead_of_file(tmp_path):
    directory = tmp_path / 'keys_dir'
    directory.mkdir()
    with pytest.raises(KeyManagerFileError) as exc:
        KeyManager(directory)
    assert 'not a file' in str(exc.value)


def test_not_utf8(tmp_path):
    bad = tmp_path / 'latin1.json'
    bad.write_bytes(b'[\xff]')
    with pytest.raises(KeyManagerFileError) as exc:
        KeyManager(bad)
    assert 'UTF-8' in str(exc.value)


def test_invalid_json():
    p = data_file('invalid_json.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()
    assert isinstance(exc.value.__cause__, ValidationError)


def test_wrong_root_array_rejected():
    p = data_file('wrong_root_array.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


def test_wrong_root_object_missing_keys():
    p = data_file('wrong_root_object.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


def test_missing_keys_field():
    p = data_file('missing_keys_field.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


def test_empty_array():
    p = data_file('empty_array.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    msg = str(exc.value)
    assert 'empty' in msg.lower()


def test_entry_not_object():
    p = data_file('entry_not_object.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


def test_missing_api_key_field():
    p = data_file('missing_api_key.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


def test_extra_property_on_credential():
    p = data_file('extra_property.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


def test_wrong_id_type():
    p = data_file('wrong_id_type.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


def test_wrong_api_key_type():
    p = data_file('wrong_api_key_type.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()


@pytest.mark.parametrize(
    'fixture',
    [
        'blank_id.json',
        'blank_api_key.json',
        'blank_api_key_whitespace.json',
    ],
)
def test_blank_or_whitespace_id_or_api_key_rejected(fixture):
    p = data_file(fixture)
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    assert 'invalid json' in str(exc.value).lower()
    assert isinstance(exc.value.__cause__, ValidationError)


def test_duplicate_id():
    p = data_file('duplicate_id.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    msg = str(exc.value)
    assert 'duplicate id' in msg.lower()


def test_duplicate_api_key():
    p = data_file('duplicate_api_key.json')
    with pytest.raises(KeyManagerJsonError) as exc:
        KeyManager(p)
    msg = str(exc.value).lower()
    assert 'duplicate api_key' in msg


def test_seconds_to_sleep_without_get_next_is_conservative():
    km = KeyManager(data_file('valid_one.json'))
    assert km.seconds_to_sleep() == pytest.approx(3.6)


def test_valid_one_key_loads_and_round_robin():
    km = KeyManager(data_file('valid_one.json'))
    assert km.key_count == 1
    assert km.calls_per_hour_per_key == DEFAULT_CALLS_PER_HOUR_PER_KEY
    cred = km.get_next()
    assert cred == KeyCredential(
        id='only',
        api_key='VuyuxjcxoIuIAJkP7JuIOh7sQWTNkugxKzuYSdGu',
    )
    assert km.get_next().id == 'only'


def test_valid_one_key_pacing():
    km = KeyManager(data_file('valid_one.json'))
    expected = 3600 / DEFAULT_CALLS_PER_HOUR_PER_KEY / 1
    with patch('mirrclient.key_manager.time.monotonic', return_value=0.0):
        km.get_next()
        assert km.seconds_to_sleep() == pytest.approx(expected)


def test_valid_multiple_keys_round_robin():
    km = KeyManager(data_file('valid_multiple.json'))
    assert km.key_count == 3
    order = [km.get_next().id for _ in range(7)]
    assert order == [
        'alpha',
        'beta',
        'gamma',
        'alpha',
        'beta',
        'gamma',
        'alpha',
    ]


def test_valid_multiple_keys_pacing():
    km = KeyManager(data_file('valid_multiple.json'))
    expected = 3600 / DEFAULT_CALLS_PER_HOUR_PER_KEY / 3
    with patch('mirrclient.key_manager.time.monotonic', return_value=0.0):
        km.get_next()
        assert km.seconds_to_sleep() == pytest.approx(expected)


def test_calls_per_hour_per_key_from_file():
    km = KeyManager(data_file('valid_calls_per_hour.json'))
    assert km.calls_per_hour_per_key == 500
    with patch('mirrclient.key_manager.time.monotonic', return_value=0.0):
        km.get_next()
        assert km.seconds_to_sleep() == pytest.approx(7.2)


def test_seconds_to_sleep_accounts_for_elapsed_wall_clock():
    km = KeyManager(data_file('valid_one.json'))
    target = 3600 / DEFAULT_CALLS_PER_HOUR_PER_KEY
    with patch('mirrclient.key_manager.time.monotonic', side_effect=[0.0, 2.5]):
        km.get_next()
        assert km.seconds_to_sleep() == pytest.approx(target - 2.5)


def test_seconds_to_sleep_never_negative():
    km = KeyManager(data_file('valid_one.json'))
    with patch('mirrclient.key_manager.time.monotonic', side_effect=[0.0, 100.0]):
        km.get_next()
        assert km.seconds_to_sleep() == 0.0
