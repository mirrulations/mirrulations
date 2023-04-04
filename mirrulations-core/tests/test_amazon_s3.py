import os
import boto3
from moto import mock_s3
from pytest import fixture
from mirrcore.amazon_s3 import AmazonS3


def create_mock_mirrulations_bucket():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    return conn


@fixture(autouse=True)
def mock_env():
    os.environ['AWS_ACCESS_KEY'] = 'test_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'


def test_get_credentials():
    assert AmazonS3().get_credentials() is True


@mock_s3
def test_get_s3_client():
    assert AmazonS3().get_s3_client()


def test_get_s3_client_no_env_variables_present():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    assert AmazonS3().get_credentials() is False


@mock_s3
def test_put_text_to_bucket():
    conn = create_mock_mirrulations_bucket()
    s3_bucket = AmazonS3()
    test_data = {
        "data": "test"
    }
    test_path = "data/test"
    response = s3_bucket.put_text_s3("test-mirrulations1",
                                     test_path, test_data)
    body = conn.Object("test-mirrulations1", "data/test").get()["Body"] \
                                                         .read() \
                                                         .decode("utf-8")
    assert body == '{"data": "test"}'
    assert response["ResponseMetadata"]['HTTPStatusCode'] == 200


@mock_s3
def test_put_binary_to_bucket():
    conn = create_mock_mirrulations_bucket()
    s3_bucket = AmazonS3()
    test_data = b'\x17'
    test_path = "data/test"
    response = s3_bucket.put_binary_s3("test-mirrulations1",
                                       test_path, test_data)
    body = conn.Object("test-mirrulations1",
                       "data/test").get()["Body"].read().decode("utf-8")
    assert body == '\x17'
    assert response["ResponseMetadata"]['HTTPStatusCode'] == 200
