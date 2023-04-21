import boto3
import datetime

class BucketSize:

    def get_bucket_size(bucket_name: str, region: str):
        cloudwatch = boto3.client("cloudwatch", region_name=region)
        result = cloudwatch.get_metric_statistics(
            Namespace="AWS/S3",
            Dimensions=[{"Name": "BucketName", "Value": bucket_name},
                        {"Name": "StorageType", "Value": "StandardStorage"}],
            MetricName="BucketSizeBytes",
            StartTime=datetime.now() - timedelta(2),
            EndTime=datetime.now(),
            Period=86400,
            Statistics=['Average'],
        )
        return result["Datapoints"][0]["Average"]
