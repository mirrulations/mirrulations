"""Scenario tests for mirrclient.key_manager.KeyManager."""

from pathlib import Path

import pytest

from pydantic import ValidationError

from mirrclient.key_manager import (
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


def test_wrong_root_not_array():
    p = data_file('wrong_root_object.json')
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


def test_valid_one_key_loads_and_paces():
    km = KeyManager(data_file('valid_one.json'))
    assert km.key_count == 1
    cred = km.get_next()
    assert cred == KeyCredential(
        id='only',
        api_key='VuyuxjcxoIuIAJkP7JuIOh7sQWTNkugxKzuYSdGu',
    )
    assert km.get_next().id == 'only'
    assert km.seconds_between_api_calls() == pytest.approx(3.6)


def test_valid_multiple_keys_round_robin_and_pacing():
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
    assert km.seconds_between_api_calls() == pytest.approx(1.2)
