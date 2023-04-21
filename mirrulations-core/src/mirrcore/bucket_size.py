import boto3
from datetime import datetime, timedelta


class BucketSize:

    def get_bucket_size(bucket_name: str, region: str):
        now = datetime.datetime.now()

        bucket_name = ...

        cloudwatch = boto3.client("cloudwatch", region_name=region)
        result = cloudwatch.get_metric_statistics(
            Namespace="AWS/S3",
            Dimensions=[{"Name": "BucketName", "Value": bucket_name},
                        {"Name": "StorageType", "Value": "StandardStorage"}],
            MetricName="BucketSizeBytes",
            StartTime=datetime.now() - timedelta(1),
            EndTime=datetime.now(),
            Period=86400,
            Statistics=['Average'],
            Unit='Bytes'
        )
        return result["Datapoints"][0]["Average"]
