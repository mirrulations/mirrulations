import os
import json
from dotenv import load_dotenv
import boto3


class S3Saver():
    """
    A class which handles saving to an S3 bucket
    ...
    Methods
    -------
    get_s3_client()

    get_credentials() -> boto3.Client

    save_json(path = string, data = dict)

    save_binary(path = string, binary = bytes)

    """
    def __init__(self, bucket_name="mirrulations"):
        """
        Constructor for S3Saver
        Gets AWS credentials from .env file
        Establishes S3 client connection
        Sets the bucket name (default='mirrulations')

        Parameters
        -------
        bucket_name : str
            Name of the bucket to write data to.
        """
        self.access_key = None
        self.secret_access_key = None
        self.s3_client = self.get_s3_client()
        self.bucket_name = bucket_name

    def get_s3_client(self):
        """
        Returns S3 client connection using aws credentials
        """
        if self.get_credentials() is False:
            print("No AWS credentials provided, Unable to write to S3.")
            return False
        return boto3.client(
                    's3',
                    region_name='us-east-1',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_access_key
                    )

    def get_credentials(self):
        """
        Loads aws credentials from .env file
        Saves credentials to instance variables

        """
        load_dotenv()
        self.access_key = os.getenv("AWS_ACCESS_KEY")
        self.secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        return (self.access_key is not None and
                self.secret_access_key is not None)

    def save_json(self, path, data):
        """
        Saves json file to Amazon S3 bucket
        Bucket Structure: /AGENCYID/path/to/item

        Parameters
        -------
        path : str
            Where to save the data to in the S3 bucket
            Ex path: bucket/Agency/

        data : dict
            The json as a dict to save.
        """
        path = path.replace("/data/", "")
        if self.s3_client is False:
            return False
        response = self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=json.dumps(data["results"])
            )
        print(f"Wrote json to S3: {path}")
        return response

    def save_binary(self, path, binary):
        """
        Saves json file to Amazon S3 bucket
        Bucket Structure: /AGENCYID/path/to/item

        Parameters
        -------
        path : str
            Where to save the data to in the S3 bucket

        binary : bytes
            The binary response.content returns
        """
        path = path.replace("/data/", "")
        if self.s3_client is False:
            return False
        response = self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=binary)
        print(f"Wrote binary to S3: {path}")
        return response

    def save_text(self, path, text):
        """
        Saves extracted text to Amazon S3 bucket
        Bucket Structure: /AGENCYID/path/to/item

        Parameters
        -------
        path : str
            Where to save the data to in the S3 bucket

        text : str
            Extracted text to be saved
        """
        path = path.replace("/data/", "")
        if self.s3_client is False:
            return False
        response = self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=text)
        print(f"Wrote extracted text to S3: {path}")
        return response
