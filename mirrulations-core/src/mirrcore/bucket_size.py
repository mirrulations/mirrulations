import boto3
from datetime import datetime, timedelta


class BucketSize:
    """A class which handles getting the size of the bucket
    ...
    Methods
    -------
    get_bucket_size()
    """

    def get_bucket_size():
        """Returns the size of the bucket in bytes"""
        bucket_name = 'mirrulations'
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        end_time = now

        cloudwatch = boto3.client("cloudwatch")
        result = cloudwatch.get_metric_statistics(
            Namespace="AWS/S3",
            Dimensions=[{"Name": "BucketName", "Value": bucket_name},
                        {"Name": "StorageType", "Value": "StandardStorage"}],
            MetricName="BucketSizeBytes",
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Average'],
            Unit='Bytes'
        )
        return result["Datapoints"][0]["Average"]
