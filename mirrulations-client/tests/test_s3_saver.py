import os
import boto3
from moto import mock_s3
from pytest import fixture
from mirrclient.s3_saver import S3Saver


def create_mock_mirrulations_bucket():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    return conn


@fixture(autouse=True)
def mock_env():
    os.environ['AWS_ACCESS_KEY'] = 'test_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'


def test_get_credentials():
    assert S3Saver().get_credentials() is True


@mock_s3
def test_get_s3_client():
    assert S3Saver().get_s3_client()


def test_get_s3_client_no_env_variables_present():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    assert S3Saver().get_credentials() is False


def test_try_saving_json_without_credentials(capsys):
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    s3_saver = S3Saver()
    s3_saver.save_json("path", "json")
    assert s3_saver.get_credentials() is False
    captured = capsys.readouterr()
    print_data = [
        'No AWS credentials provided, Unable to write to S3.\n',
    ]
    assert captured.out == "".join(print_data)


def test_try_saving_binary_without_credentials(capsys):
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    s3_saver = S3Saver()
    s3_saver.save_binary("path", "json")
    assert s3_saver.get_credentials() is False
    captured = capsys.readouterr()
    print_data = [
        'No AWS credentials provided, Unable to write to S3.\n',
    ]
    assert captured.out == "".join(print_data)


@mock_s3
def test_save_json_to_bucket():
    conn = create_mock_mirrulations_bucket()
    s3_bucket = S3Saver(bucket_name="test-mirrulations1")
    test_data = {
        "results": 'test'
    }
    test_path = "data/test.json"
    response = s3_bucket.save_json(test_path, test_data)
    body = conn.Object("test-mirrulations1",
                       "data/test.json").get()["Body"].read()\
        .decode("utf-8").strip('/"')
    assert body == test_data["results"]
    assert response["ResponseMetadata"]['HTTPStatusCode'] == 200


@mock_s3
def test_save_binary_to_bucket():
    conn = create_mock_mirrulations_bucket()
    s3_bucket = S3Saver(bucket_name="test-mirrulations1")
    test_data = b'\x17'
    test_path = "data/test.binary"
    response = s3_bucket.save_binary(test_path, test_data)
    body = conn.Object("test-mirrulations1",
                       "data/test.binary").get()["Body"].read().decode("utf-8")
    assert body == '\x17'
    assert response["ResponseMetadata"]['HTTPStatusCode'] == 200


@mock_s3
def test_save_text_to_bucket():
    conn = create_mock_mirrulations_bucket()
    s3_bucket = S3Saver(bucket_name="test-mirrulations1")
    test_data = "test"
    test_path = "data/test.txt"
    response = s3_bucket.save_text(test_path, test_data)
    body = conn.Object("test-mirrulations1",
                       "data/test.txt").get()["Body"].read().decode("utf-8")
    assert body == 'test'
    assert response["ResponseMetadata"]['HTTPStatusCode'] == 200


def test_save_json_to_s3_no_credentials_returns_false(capsys):
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    assert S3Saver().save_json("test", "test") is False
    assert capsys.readouterr().out == "No AWS credentials provided, "\
                                      "Unable to write to S3.\n"


def test_save_binary_to_s3_no_credentials_returns_false(capsys):
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    assert S3Saver().save_binary("test", "test") is False
    assert capsys.readouterr().out == "No AWS credentials provided, "\
                                      "Unable to write to S3.\n"


def test_save_text_to_s3_no_credentials_returns_false(capsys):
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    assert S3Saver().save_text("test", "test") is False
    assert capsys.readouterr().out == "No AWS credentials provided, "\
                                      "Unable to write to S3.\n"
