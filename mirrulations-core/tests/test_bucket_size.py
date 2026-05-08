from unittest.mock import MagicMock, patch
from datetime import UTC, datetime
import os
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

    BucketSizeBytes exists per StorageType; get_bucket_size lists metrics
    and sums the latest daily Average for each series.
    """
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            'Metrics': [
                {
                    'Namespace': 'AWS/S3',
                    'MetricName': 'BucketSizeBytes',
                    'Dimensions': [
                        {'Name': 'BucketName', 'Value': 'mirrulations'},
                        {'Name': 'StorageType', 'Value': 'StandardStorage'},
                    ],
                },
                {
                    'Namespace': 'AWS/S3',
                    'MetricName': 'BucketSizeBytes',
                    'Dimensions': [
                        {'Name': 'BucketName', 'Value': 'mirrulations'},
                        {'Name': 'StorageType',
                         'Value': 'IntelligentTieringIAStorage'},
                    ],
                },
            ]
        },
    ]
    client.get_paginator.return_value = paginator

    # Bucket total: 1500.5 GiB (1024³, same divisor as BucketSize).
    # Two StorageTypes each contribute half of that total bytes.
    bytes_per_gib = 1 << 30
    total_bucket_bytes = int(1500.5 * bytes_per_gib)
    bytes_per_storage_type = total_bucket_bytes // 2

    ts = datetime(2026, 5, 6, tzinfo=UTC)

    client.get_metric_statistics.return_value = {
        'Datapoints': [{'Timestamp': ts, 'Average': bytes_per_storage_type}],
    }

    mock_method.return_value = client

    # math.ceil(1500.5 binary GB) == 1501
    assert BucketSize.get_bucket_size() == 1501
    client.get_paginator.assert_called_once_with('list_metrics')
    kwargs0 = client.get_metric_statistics.call_args_list[0].kwargs
    assert kwargs0["StartTime"].tzinfo is UTC
    assert kwargs0["EndTime"].tzinfo is UTC
    assert len(client.get_metric_statistics.call_args_list) == 2
