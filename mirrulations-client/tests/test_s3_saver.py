import os
from unittest.mock import patch
import boto3
from moto import mock_aws
import pytest
from botocore.exceptions import ClientError
from mirrclient.s3_saver import S3Saver
from mirrclient.exceptions import SaveError


def create_mock_mirrulations_bucket():
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-mirrulations1")
    return conn


@pytest.fixture(autouse=True)
def mock_env():
    os.environ['AWS_ACCESS_KEY'] = 'test_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'


def test_get_credentials():
    assert S3Saver().get_credentials() is True


@mock_aws
def test_get_s3_client():
    assert S3Saver().get_s3_client()


def test_get_s3_client_no_env_variables_present():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    assert S3Saver().get_credentials() is False


def test_try_saving_json_without_credentials():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    s3_saver = S3Saver()
    assert s3_saver.get_credentials() is False
    with pytest.raises(SaveError, match='No AWS credentials'):
        s3_saver.save_json("path", {"results": {}})


def test_try_saving_binary_without_credentials():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    s3_saver = S3Saver()
    assert s3_saver.get_credentials() is False
    with pytest.raises(SaveError, match='No AWS credentials'):
        s3_saver.save_binary("path", b"x")


@mock_aws
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


@mock_aws
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


@mock_aws
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


def test_save_json_to_s3_no_credentials_raises():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    with pytest.raises(SaveError, match='No AWS credentials'):
        S3Saver().save_json("test", {"results": {}})


def test_save_binary_to_s3_no_credentials_raises():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    with pytest.raises(SaveError, match='No AWS credentials'):
        S3Saver().save_binary("test", b"x")


def test_save_text_to_s3_no_credentials_raises():
    del os.environ['AWS_ACCESS_KEY']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    with pytest.raises(SaveError, match='No AWS credentials'):
        S3Saver().save_text("test", "text")


@mock_aws
def test_save_json_access_denied_raises_and_no_write():
    conn = create_mock_mirrulations_bucket()
    s3_saver = S3Saver(bucket_name="test-mirrulations1")
    error = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        "PutObject"
    )
    with patch.object(s3_saver.s3_client, "put_object", side_effect=error):
        with pytest.raises(SaveError, match='put_object failed'):
            s3_saver.save_json("nope.json", {"results": "bar"})
    assert len(list(conn.Bucket("test-mirrulations1").objects.all())) == 0


@mock_aws
def test_save_binary_access_denied_raises_and_no_write():
    conn = create_mock_mirrulations_bucket()
    s3_saver = S3Saver(bucket_name="test-mirrulations1")
    error = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        "PutObject"
    )
    with patch.object(s3_saver.s3_client, "put_object", side_effect=error):
        with pytest.raises(SaveError, match='put_object failed'):
            s3_saver.save_binary("data/forbidden.binary", b"\x17")
    assert len(list(conn.Bucket("test-mirrulations1").objects.all())) == 0


@mock_aws
def test_save_text_access_denied_raises_and_no_write():
    conn = create_mock_mirrulations_bucket()
    s3_saver = S3Saver(bucket_name="test-mirrulations1")
    error = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        "PutObject"
    )
    with patch.object(s3_saver.s3_client, "put_object", side_effect=error):
        with pytest.raises(SaveError, match='put_object failed'):
            s3_saver.save_text("data/forbidden.txt", "test")
    assert len(list(conn.Bucket("test-mirrulations1").objects.all())) == 0


@mock_aws
def test_s3_saver_creates_file_with_one_in_name_when_json_exists():
    """When a JSON key already exists, S3Saver writes the new payload
       at ``…(1).json``.
    """
    conn = create_mock_mirrulations_bucket()
    bucket = conn.Bucket("test-mirrulations1")
    bucket.put_object(Key="raw-data/x/doc.json", Body=b'{}')
    s3_saver = S3Saver(bucket_name="test-mirrulations1")
    payload = {"results": {"data": "new"}}
    s3_saver.save_json("raw-data/x/doc.json", payload)
    keys = {obj.key for obj in bucket.objects.all()}
    assert keys == {"raw-data/x/doc.json", "raw-data/x/doc(1).json"}
    body = conn.Object("test-mirrulations1", "raw-data/x/doc(1).json").get()[
        "Body"].read().decode("utf-8")
    assert body == '{"data": "new"}'


@mock_aws
def test_s3_saver_creates_file_with_four_in_name_when_one_two_three_exist():
    """When canonical and ``(1)``…``(3)`` exist, S3Saver writes at ``…(4).json``."""
    conn = create_mock_mirrulations_bucket()
    bucket = conn.Bucket("test-mirrulations1")
    for key in (
        "a/b/item.json",
        "a/b/item(1).json",
        "a/b/item(2).json",
        "a/b/item(3).json",
    ):
        bucket.put_object(Key=key, Body=b'{}')
    s3_saver = S3Saver(bucket_name="test-mirrulations1")
    payload = {"results": {"slot": 4}}
    s3_saver.save_json("a/b/item.json", payload)
    keys = {obj.key for obj in bucket.objects.all()}
    assert keys == {
        "a/b/item.json",
        "a/b/item(1).json",
        "a/b/item(2).json",
        "a/b/item(3).json",
        "a/b/item(4).json",
    }
    body = conn.Object("test-mirrulations1", "a/b/item(4).json").get()[
        "Body"].read().decode("utf-8")
    assert body == '{"slot": 4}'
