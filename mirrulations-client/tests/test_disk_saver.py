from json import dumps
import logging
from unittest.mock import patch, mock_open

import pytest

from mirrclient.disk_saver import DiskSaver
from mirrclient.exceptions import SaveError


def test_save_json_writes_first_alternate_when_base_exists_and_differs():
    path = '/USTR/file.json'
    payload = {'data': 'new'}
    data = {'results': payload}
    saver = DiskSaver()

    def exists_side_effect(p):
        return p == path

    with patch(
            'mirrclient.disk_saver.os.path.exists',
            side_effect=exists_side_effect):
        with patch.object(saver, 'make_path'):
            with patch.object(
                    saver, 'open_json_file', return_value={'data': 'old'}):
                with patch.object(saver, 'save_to_disk') as mock_save:
                    saver.save_json(path, data)
    mock_save.assert_called_once_with('/USTR/file(1).json', payload)


def test_save_json_skips_when_numbered_file_already_has_same_payload():
    """Same payload already stored at file(2).json — do not write again."""
    path = '/USTR/file.json'
    payload = {'v': 2}
    data = {'results': payload}
    saver = DiskSaver()
    contents_by_path = {
        '/USTR/file.json': {'data': 'old'},
        '/USTR/file(1).json': {'x': 1},
        '/USTR/file(2).json': payload,
    }

    def exists_side_effect(p):
        return p in contents_by_path

    def open_json_side_effect(p):
        return contents_by_path[p]

    with patch(
            'mirrclient.disk_saver.os.path.exists',
            side_effect=exists_side_effect):
        with patch.object(saver, 'make_path'):
            with patch.object(
                    saver, 'open_json_file',
                    side_effect=open_json_side_effect):
                with patch.object(saver, 'save_to_disk') as mock_save:
                    saver.save_json(path, data)
    mock_save.assert_not_called()


def test_save_path_directory_does_not_already_exist():
    with patch('os.makedirs') as mock_dir:
        saver = DiskSaver()
        saver.make_path('/USTR')
        mock_dir.assert_called_once_with('/USTR')


def test_save_json():
    saver = DiskSaver()
    path = '/USTR/file.json'
    data = {'results': 'Hello world'}
    with patch('mirrclient.disk_saver.open', mock_open()) as mocked_file:
        with patch('os.makedirs') as mock_dir:
            saver.save_json(path, data)
            mock_dir.assert_called_once_with('/USTR')
            mocked_file.assert_called_once_with(path, 'x', encoding='utf8')
            mocked_file().write.assert_called_once_with(dumps(data['results']))


def test_save_binary():
    saver = DiskSaver()
    path = '/USTR/file.pdf'
    data = 'Some Binary'
    with patch('mirrclient.disk_saver.open', mock_open()) as mocked_file:
        with patch('os.makedirs') as mock_dir:
            saver.save_binary(path, data)
            mock_dir.assert_called_once_with('/USTR')
            mocked_file.assert_called_once_with(path, 'wb')
            mocked_file().write.assert_called_once_with(data)


def test_save_text():
    saver = DiskSaver()
    path = '/USTR/file.txt'
    data = 'text'
    with patch('mirrclient.disk_saver.open', mock_open()) as mocked_file:
        with patch('os.makedirs') as mock_dir:
            saver.save_text(path, data)
            mock_dir.assert_called_once_with('/USTR')
            mocked_file.assert_called_once_with(path, 'w', encoding="utf-8")
            mocked_file().write.assert_called_once_with(data)


def test_is_duplicate_is_a_duplicate():
    existing = {'is_duplicate': True}
    new = {'is_duplicate': True}
    saver = DiskSaver()
    is_duplicate = saver.is_duplicate(existing, new)
    assert is_duplicate


def test_is_duplicate_is_not_a_duplicate():
    existing = {'is_duplicate': True}
    new = {'is_duplicate': False}
    saver = DiskSaver()
    is_duplicate = saver.is_duplicate(existing, new)
    assert not is_duplicate


def test_open_json():
    saver = DiskSaver()
    path = 'data/USTR/file.json'
    data = {'results': 'Hello world'}
    mock = mock_open(read_data=dumps(data))
    with patch('mirrclient.disk_saver.open', mock) as mocked_file:
        saver.open_json_file(path)
        mocked_file.assert_called_once_with(path, encoding='utf8')


def test_save_json_numbered_uses_open_x_on_first_free_slot():
    path = 'data/USTR/file.json'
    payload = {'data': 'Hello world'}
    data = {'results': payload}
    saver = DiskSaver()

    def exists_side_effect(p):
        return p == path

    with patch(
            'mirrclient.disk_saver.os.path.exists',
            side_effect=exists_side_effect):
        with patch.object(
                saver, 'open_json_file', return_value={'other': True}):
            with patch(
                    'mirrclient.disk_saver.open', mock_open()) as mocked_file:
                saver.save_json(path, data)
            mocked_file.assert_called_once_with(
                'data/USTR/file(1).json', 'x', encoding='utf8')


def test_save_json_raises_save_error_when_write_fails():
    saver = DiskSaver()
    with patch.object(saver, 'make_path'):
        with patch('mirrclient.disk_saver.os.path.exists', return_value=False):
            with patch(
                    'mirrclient.disk_saver.open',
                    side_effect=OSError('denied')):
                with pytest.raises(SaveError) as err:
                    saver.save_json('/x/y.json', {'results': {}})
    assert 'Disk save_to_disk failed' in str(err.value)
    assert 'denied' in str(err.value)


def test_save_binary_raises_save_error_when_write_fails():
    saver = DiskSaver()
    with patch.object(saver, 'make_path'):
        with patch('mirrclient.disk_saver.open', side_effect=PermissionError('no')):
            with pytest.raises(SaveError) as err:
                saver.save_binary('/x/y.bin', b'd')
    assert 'Disk save_binary failed' in str(err.value)


def test_save_text_raises_save_error_when_write_fails():
    saver = DiskSaver()
    with patch.object(saver, 'make_path'):
        with patch('mirrclient.disk_saver.open', side_effect=OSError('bad')):
            with pytest.raises(SaveError) as err:
                saver.save_text('/x/y.txt', 't')
    assert 'Disk save_text failed' in str(err.value)


def test_save_json_propagates_save_error_without_double_wrap():
    saver = DiskSaver()
    with patch.object(saver, 'make_path'):
        with patch(
                'mirrclient.disk_saver.os.path.exists', return_value=False):
            with patch.object(
                    saver,
                    'save_to_disk',
                    side_effect=SaveError('preserved')):
                with pytest.raises(SaveError, match='preserved'):
                    saver.save_json('/x/y.json', {'results': {}})


def test_do_not_save_duplicate_data(caplog):
    path = '/USTR/file.json'
    data = {'results': {'data': 'Hello world'}}
    saver = DiskSaver()
    with patch('mirrclient.disk_saver.os.path.exists', return_value=True):
        with patch.object(
                saver, 'open_json_file',
                return_value=data['results']):
            with patch('os.makedirs') as mock_dir:
                with patch.object(saver, 'save_to_disk') as mock_save:
                    caplog.set_level(logging.DEBUG)
                    saver.save_json(path, data)
                    mock_dir.assert_called_once_with('/USTR')
                    mock_save.assert_not_called()
                    msgs = '\n'.join(r.message for r in caplog.records)
                    assert 'unchanged skip write' in msgs


def test_save_tombstone_writes_single_http_line(tmp_path):
    saver = DiskSaver()
    path = tmp_path / 'nested' / 'doc_UNAVAILABLE'
    saver.save_tombstone(str(path), 404)
    assert path.read_text(encoding='utf-8') == 'HTTP 404'


def test_save_tombstone_overwrites_existing(tmp_path):
    saver = DiskSaver()
    path = tmp_path / 't_UNAVAILABLE'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('HTTP 500', encoding='utf-8')
    saver.save_tombstone(str(path), 503)
    assert path.read_text(encoding='utf-8') == 'HTTP 503'
