from json import dumps
from unittest.mock import patch, mock_open
import os
from pytest import fixture
from moto import mock_s3
import boto3
from mirrclient.saver import Saver
from mirrclient.s3_saver import S3Saver
from mirrclient.disk_saver import DiskSaver


@fixture(autouse=True)
def mock_env():
    os.environ['AWS_ACCESS_KEY'] = 'test_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'


def test_saving_to_disk():
    test_path = '/USTR/file.json'
    test_data = {'results': 'Hello world'}

    with patch('mirrclient.disk_saver.open', mock_open()) as mocked_file:
        with patch('os.makedirs') as mock_dir:
            saver = Saver(savers=[DiskSaver()])
            saver.save_json(test_path, test_data)
            mock_dir.assert_called_once_with('/USTR')
            mocked_file.assert_called_once_with(test_path, 'x',
                                                encoding='utf8')
            mocked_file().write.assert_called_once_with(
                dumps(test_data['results']))


@mock_s3
def test_saving_to_s3():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    saver = Saver(savers=[
        S3Saver(bucket_name="test-mirrulations1")])
    test_data = {
        "results": "test"
    }
    test_path = "data/test.json"
    saver.save_json(test_path, test_data)
    body = conn.Object("test-mirrulations1",
                       "data/test.json").get()["Body"].read()\
        .decode("utf-8").strip('/"')
    assert body == test_data["results"]


@mock_s3
def test_saver_saves_json_to_multiple_places():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    test_path = '/USTR/file.json'
    test_data = {'results': 'Hello world'}

    with patch('mirrclient.disk_saver.open', mock_open()) as mocked_file:
        with patch('os.makedirs') as mock_dir:
            saver = Saver(savers=[
                DiskSaver(),
                S3Saver(bucket_name="test-mirrulations1")])
            saver.save_json(test_path, test_data)
            mock_dir.assert_called_once_with('/USTR')
            mocked_file.assert_called_once_with(test_path, 'x',
                                                encoding='utf8')
            mocked_file().write.assert_called_once_with(
                dumps(test_data['results']))
            body = conn.Object("test-mirrulations1",
                               "/USTR/file.json").get()["Body"].read()\
                .decode("utf-8").strip('/"')
            assert body == test_data["results"]


@mock_s3
def test_saver_saves_binary_to_multiple_places():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    test_path = '/USTR/file.pdf'
    test_data = b'\x17'

    with patch('mirrclient.disk_saver.open', mock_open()) as mocked_file:
        with patch('os.makedirs') as mock_dir:
            saver = Saver(savers=[
                DiskSaver(),
                S3Saver(bucket_name="test-mirrulations1")])
            saver.save_binary(test_path, test_data)
            mock_dir.assert_called_once_with('/USTR')
            mocked_file.assert_called_once_with(test_path, 'wb')
            mocked_file().write.assert_called_once_with(test_data)
            body = conn.Object("test-mirrulations1",
                               "/USTR/file.pdf").get()["Body"].read()\
                .decode("utf-8")
            assert body == '\x17'


@mock_s3
def test_saver_saves_text_to_multiple_places():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    test_path = '/USTR/file.txt'
    test_data = 'test'

    with patch('mirrclient.disk_saver.open', mock_open()) as mocked_file:
        with patch('os.makedirs') as mock_dir:
            saver = Saver(savers=[
                DiskSaver(),
                S3Saver(bucket_name="test-mirrulations1")])
            saver.save_text(test_path, test_data)
            mock_dir.assert_called_once_with('/USTR')
            mocked_file.assert_called_once_with(test_path, 'w',
                                                encoding="utf-8")
            mocked_file().write.assert_called_once_with(test_data)
            body = conn.Object("test-mirrulations1",
                               "/USTR/file.txt").get()["Body"].read()\
                .decode("utf-8")
            assert body == test_data
