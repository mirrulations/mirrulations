import logging
import os
import json
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

from mirrclient.exceptions import SaveError

_log = logging.getLogger(__name__)


def _s3_object_key(path):
    """Strip leading slash; drop legacy ``/data/`` prefix from older clients."""
    if path.startswith('/data/'):
        path = path[6:]
    return path.lstrip('/')


def _head_missing_error_code(code):
    return code in ('404', 'NoSuchKey', 'NotFound')


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

    def _s3_object_exists(self, key):
        """Return True if ``key`` is present; False if absent.
           Other errors -> SaveError.
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as exc:
            code = exc.response.get('Error', {}).get('Code', '')
            if _head_missing_error_code(code):
                return False
            raise SaveError(
                f"S3 head_object failed for s3://{self.bucket_name}/{key}"
            ) from exc

    def _resolve_json_write_key(self, key):
        """
        Use ``key`` when free. If it exists, use the next free ``stem(n).json``.
        Keys that do not end with ``.json`` are written as-is (overwrite).
        """
        if not key.endswith('.json'):
            return key
        if not self._s3_object_exists(key):
            return key
        stem = key.removesuffix('.json')
        counter = 1
        while True:
            candidate = f'{stem}({counter}).json'
            if not self._s3_object_exists(candidate):
                return candidate
            counter += 1

    def save_json(self, path, data):
        """
        Saves json file to Amazon S3 bucket
        Bucket Structure: /AGENCYID/path/to/item

        If the canonical ``*.json`` key already exists, writes to the next free
        ``*``(1).json``, ``(2).json``, … slot (existence only; no body compare).

        Parameters
        -------
        path : str
            Where to save the data to in the S3 bucket
            Ex path: bucket/Agency/

        data : dict
            The json as a dict to save.
        """
        key = _s3_object_key(path)
        if self.s3_client is False:
            raise SaveError(
                "No AWS credentials provided; cannot write to S3."
            ) from None
        try:
            write_key = self._resolve_json_write_key(key)
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=write_key,
                Body=json.dumps(data["results"])
                )
            _log.debug(
                'S3 wrote json key=%s bucket=%s', write_key, self.bucket_name)
            return response
        except ClientError as exc:
            raise SaveError(
                f"S3 put_object failed for s3://{self.bucket_name}/{write_key}"
            ) from exc

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
        path = _s3_object_key(path)
        if self.s3_client is False:
            raise SaveError(
                "No AWS credentials provided; cannot write to S3."
            ) from None
        try:
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=path,
                Body=binary)
            _log.debug('S3 wrote binary key=%s bucket=%s', path, self.bucket_name)
            return response
        except ClientError as exc:
            raise SaveError(
                f"S3 put_object failed for s3://{self.bucket_name}/{path}"
            ) from exc

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
        path = _s3_object_key(path)
        if self.s3_client is False:
            raise SaveError(
                "No AWS credentials provided; cannot write to S3."
            ) from None
        try:
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=path,
                Body=text)
            _log.debug('S3 wrote text key=%s bucket=%s', path, self.bucket_name)
            return response
        except ClientError as exc:
            raise SaveError(
                f"S3 put_object failed for s3://{self.bucket_name}/{path}"
            ) from exc
