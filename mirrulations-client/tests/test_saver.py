from json import dumps
from unittest.mock import patch, mock_open, MagicMock
import os
from mirrclient.saver import Saver
from pytest import fixture, mark
import boto3
from moto import mock_s3


@fixture(name='save_duplicate_json')
def mock_save_duplicate(mocker):
    mocker.patch.object(
        Saver,
        'save_duplicate_json',
        return_value=None
    )


@fixture(name='duplicate_check')
def mock_check_for_duplicate(mocker):
    mocker.patch.object(
        Saver,
        'check_for_duplicates',
        return_value=None,
    )


@fixture(name='is_duplicate')
def mock_is_duplicate(mocker):
    mocker.patch.object(
        Saver,
        'is_duplicate',
        return_value=True
    )


def test_save_path_directory_does_not_already_exist():
    with patch('os.makedirs') as mock_dir:
        saver = Saver()
        saver.make_path('/USTR')
        mock_dir.assert_called_once_with('/data/USTR')


def test_save_path_directory_already_exists(capsys):
    with patch('os.makedirs') as mock_dir:
        saver = Saver()
        mock_dir.side_effect = FileExistsError('Directory already exists')
        saver.make_path('/USTR')

        print_data = 'Directory already exists in root: /data/USTR\n'
        captured = capsys.readouterr()
        assert captured.out == print_data


def test_save_json():
    saver = Saver()
    path = 'data/USTR/file.json'
    data = {'results': 'Hello world'}

    with patch('mirrclient.saver.open', mock_open()) as mocked_file:
        saver.save_json(path, data)
        mocked_file.assert_called_once_with(path, 'x', encoding='utf8')
        mocked_file().write.assert_called_once_with(dumps(data['results']))


def test_save_attachment():
    saver = Saver()
    path = 'data/USTR/file.pdf'
    data = 'Some Binary'

    with patch('mirrclient.saver.open', mock_open()) as mocked_file:
        saver.save_attachment(path, data)
        mocked_file.assert_called_once_with(path, 'wb')
        mocked_file().write.assert_called_once_with(data)


def test_is_duplicate_is_a_duplicate():
    existing = {'is_duplicate': True}
    new = {'is_duplicate': True}
    saver = Saver()
    is_duplicate = saver.is_duplicate(existing, new)
    assert is_duplicate


def test_is_duplicate_is_not_a_duplicate():
    existing = {'is_duplicate': True}
    new = {'is_duplicate': False}
    saver = Saver()
    is_duplicate = saver.is_duplicate(existing, new)
    assert not is_duplicate


def test_open_json():
    saver = Saver()
    path = 'data/USTR/file.json'
    data = {'results': 'Hello world'}
    mock = mock_open(read_data=dumps(data))
    with patch('mirrclient.saver.open', mock) as mocked_file:
        saver.open_json_file(path)
        mocked_file.assert_called_once_with(path, encoding='utf8')


def test_save_duplicate_json():
    path = 'data/USTR/file.json'
    data = {'data': 'Hello world'}
    saver = Saver()
    mock = MagicMock()
    mock.mock_open()
    with patch('mirrclient.saver.open', mock) as mocked_file:
        saver.save_duplicate_json(path, data, 1)
        mocked_file.assert_called_once_with(f'data/USTR/file({1}).json', 'x',
                                            encoding='utf8')


@mark.usefixtures("duplicate_check")
def test_do_not_save_duplicate_data(capsys):
    path = 'data/USTR/file.json'
    data = {'results': {'data': 'Hello world'}}
    saver = Saver()
    mock = MagicMock()
    mock.return_value(True)
    with patch('os.path.exists', mock):
        saver.save_json(path, data)
        print_data = ''
        captured = capsys.readouterr()
        assert captured.out == print_data


@mark.usefixtures("duplicate_check")
def test_do_not_save_duplicate_json_data(capsys):
    path = 'data/USTR/file.json'
    data = {'results': {'data': 'Hello world'}}
    saver = Saver()
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
    saver = Saver()
    mock = mock_open(read_data=dumps(data))
    with patch('mirrclient.saver.open', mock) as mocked_file:
        saver.open_json_file(path)
        mocked_file.assert_called_once_with(path, encoding='utf8')
        saver.check_for_duplicates(path, data, 1)
        print_data = ''
        captured = capsys.readouterr()
        assert captured.out == print_data


@fixture(autouse=True)
def mock_env():
    os.environ['AWS_ACCESS_KEY'] = 'test_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'


@mock_s3
def test_save_valid_json_to_s3():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    saver = Saver()
    test_path = "testpath"
    test_json = {
        "data": {"attributes": 0}
    }
    saver.save_json_to_s3("test-mirrulations1", test_path, test_json)
    body = conn.Object("test-mirrulations1", "testpath").get()["Body"] \
                                                        .read() \
                                                        .decode("utf-8")
    assert body == '{"data": {"attributes": 0}}'


@mock_s3
def test_save_valid_attachment_to_s3():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    saver = Saver()
    test_binary_data = b"\x17"
    test_path = "testpath"
    saver.save_binary_to_s3("test-mirrulations1", test_path, test_binary_data)
    body = conn.Object("test-mirrulations1", "testpath").get()["Body"] \
                                                        .read() \
                                                        .decode("utf-8")
    assert body == '\x17'
