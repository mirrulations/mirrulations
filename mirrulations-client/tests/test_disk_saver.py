from json import dumps
from unittest.mock import patch, mock_open, MagicMock
from pytest import fixture, mark
from mirrclient.disk_saver import DiskSaver


@fixture(name='save_duplicate_json')
def mock_save_duplicate(mocker):
    mocker.patch.object(
        DiskSaver,
        'save_duplicate_json',
        return_value=None
    )


@fixture(name='duplicate_check')
def mock_check_for_duplicate(mocker):
    mocker.patch.object(
        DiskSaver,
        'check_for_duplicates',
        return_value=None,
    )


@fixture(name='is_duplicate')
def mock_is_duplicate(mocker):
    mocker.patch.object(
        DiskSaver,
        'is_duplicate',
        return_value=True
    )


def test_save_path_directory_does_not_already_exist():
    with patch('os.makedirs') as mock_dir:
        saver = DiskSaver()
        saver.make_path('/USTR')
        mock_dir.assert_called_once_with('/USTR')


def test_save_path_directory_already_exists(capsys):
    with patch('os.makedirs') as mock_dir:
        saver = DiskSaver()
        mock_dir.side_effect = FileExistsError('Directory already exists')
        saver.make_path('/USTR')

        print_data = 'Directory already exists in root: /data/USTR\n'
        captured = capsys.readouterr()
        assert captured.out == print_data


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


def test_save_duplicate_json():
    path = 'data/USTR/file.json'
    data = {'data': 'Hello world'}
    saver = DiskSaver()
    mock = MagicMock()
    mock.mock_open()
    with patch('mirrclient.disk_saver.open', mock) as mocked_file:
        saver.save_duplicate_json(path, data, 1)
        mocked_file.assert_called_once_with(f'data/USTR/file({1}).json', 'x',
                                            encoding='utf8')


@mark.usefixtures("duplicate_check")
def test_do_not_save_duplicate_data(capsys):
    path = '/USTR/file.json'
    data = {'results': {'data': 'Hello world'}}
    saver = DiskSaver()
    mock = MagicMock()
    mock.return_value(True)
    with patch('os.path.exists', mock):
        with patch('os.makedirs') as mock_dir:
            saver.save_json(path, data)
            mock_dir.assert_called_once_with('/USTR')
            print_data = ''
            captured = capsys.readouterr()
            assert captured.out == print_data


@mark.usefixtures("duplicate_check")
def test_do_not_save_duplicate_json_data(capsys):
    path = 'data/USTR/file.json'
    data = {'results': {'data': 'Hello world'}}
    saver = DiskSaver()
    mock = MagicMock()
    mock.return_value(True)
    with patch('os.path.exists', mock):
        saver.save_duplicate_json(path, data, 1)
        print_data = ''
        captured = capsys.readouterr()
        assert captured.out == print_data


@mark.usefixtures("is_duplicate")
def test_check_for_duplicates(capsys):
    path = 'data/USTR/file.json'
    data = {'data': 'Hello world'}
    saver = DiskSaver()
    mock = mock_open(read_data=dumps(data))
    with patch('mirrclient.disk_saver.open', mock) as mocked_file:
        saver.open_json_file(path)
        mocked_file.assert_called_once_with(path, encoding='utf8')
        saver.check_for_duplicates(path, data, 1)
        print_data = ''
        captured = capsys.readouterr()
        assert captured.out == print_data
