from unittest.mock import MagicMock, patch
import os
import math
from mirrcore.bucket_size import BucketSize
from pytest import fixture
from botocore.client import BaseClient


@fixture(autouse=True)
def mock_env():
    os.environ['AWS_ACCESS_KEY'] = 'test_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'


def test_get_credentials():
    """
    mocked env file with fixture
    """
    assert BucketSize.get_credentials() == ['test_key', 'test_secret_key']


def test_get_client():
    """
    test client gets created with AWS keys
    """
    client = BucketSize.get_cloudwatch_client()
    assert isinstance(client, BaseClient)


def test_empty_env_credentials():
    """
    test the process of the BucketSize class when there are no AWS credentails

    No credentials -> No client created -> Can't get metrics
    """
    os.environ['AWS_ACCESS_KEY'] = ''
    os.environ['AWS_SECRET_ACCESS_KEY'] = ''
    assert BucketSize.get_credentials() == ['', '']
    client = BucketSize.get_cloudwatch_client()
    assert not isinstance(client, BaseClient)
    assert BucketSize.get_bucket_size() is None


@patch('mirrcore.bucket_size.BucketSize.get_cloudwatch_client')
def test_get_bucket_size(mock_method):
    """
    needed the patch for mocking the return value of a static function

    Mocks the process of getting the size of a bucket with the
    get_metric_statistics function of a cloudwatch client
    """
    # Mock the CloudWatch client
    client = MagicMock()

    client.get_metric_statistics.return_value = {
        'Datapoints': [{'Average': 12345678910}]
    }

    mock_method.return_value = client

    result = math.ceil(BucketSize.get_bucket_size())

    assert result == 13  # Expected result in GB
