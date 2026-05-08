from datetime import UTC, datetime, timedelta
import os
import math
import boto3
from dotenv import load_dotenv


class BucketSize:
    """
    A class which handles getting the size of the mirrulations bucket
    on S3

    Uses cloudwatch client
    ...
    Methods
    -------
    get_bucket_size()
    """

    @staticmethod
    def get_bucket_size():
        """Returns the size of the bucket in binary gigabytes (1024³ bytes).

        S3 publishes ``BucketSizeBytes`` per ``StorageType`` (Standard,
        Intelligent-Tiering tiers, Glacier, etc.). Total size is the sum of
        the latest daily observation for each distinct series—not the sum of
        ``Datapoints`` across time for one series.
        """
        client = BucketSize.get_cloudwatch_client()
        # when client cannot establish connection to cloudwatch due to no AWS
        # credentials, return
        if not client:
            return None
        total_bytes = 0.0
        paginator = client.get_paginator("list_metrics")
        for page in paginator.paginate(
            Namespace="AWS/S3",
            MetricName="BucketSizeBytes",
            Dimensions=[{"Name": "BucketName", "Value": "mirrulations"}],
        ):
            for metric in page.get("Metrics", []):
                total_bytes += BucketSize._bytes_for_metric_series(
                    client, metric
                )

        bytes_per_gb = 1 << 30  # GiB-style GB: 1024³
        bucket_size_gb = math.ceil(total_bytes / bytes_per_gb)
        return bucket_size_gb

    @staticmethod
    def _bytes_for_metric_series(client, metric):
        dimensions = metric.get("Dimensions", [])
        stor_type = None
        for dim in dimensions:
            if dim.get("Name") == "StorageType":
                stor_type = dim.get("Value")
                break
        if stor_type is None:
            return 0.0
        result = client.get_metric_statistics(
            Namespace="AWS/S3",
            Dimensions=dimensions,
            MetricName="BucketSizeBytes",
            StartTime=datetime.now(UTC) - timedelta(days=2),
            EndTime=datetime.now(UTC),
            Period=86400,  # 1 day in seconds
            Statistics=["Average"],
            Unit="Bytes",
        )
        datapoints = result.get("Datapoints", [])
        if not datapoints:
            return 0.0
        latest = max(datapoints, key=lambda p: p["Timestamp"])
        return float(latest["Average"])

    @staticmethod
    def get_cloudwatch_client():
        """
        Returns a cloudwatch client connection

        Or None if AWS credentials are missing from env
        """
        access_key, secret_access_key = BucketSize.get_credentials()

        if access_key == '' or secret_access_key == '':
            print("No AWS credentials provided, Can't connect to cloudwatch")
            return None
        return boto3.client(
                    "cloudwatch",
                    region_name='us-east-1',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_access_key
                    )

    @staticmethod
    def get_credentials():
        """
        Loads aws credentials from .env file
        Saves credentials to instance variables
        """
        load_dotenv()
        access_key = os.getenv("AWS_ACCESS_KEY")
        secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        return [access_key, secret_access_key]
