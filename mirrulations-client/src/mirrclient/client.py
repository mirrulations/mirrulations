import time
import os
import sys
import requests
import redis
from dotenv import load_dotenv
from mirrclient.saver import Saver
from mirrclient.disk_saver import DiskSaver
from mirrclient.s3_saver import S3Saver
from mirrclient.exceptions import NoJobsAvailableException, APITimeoutException
from mirrclient.key_manager import (
    KeyCredential,
    KeyManager,
    KeyManagerFileError,
    KeyManagerJsonError,
)
from mirrcore.redis_check import load_redis
from mirrcore.path_generator import PathGenerator
from mirrcore.job_queue import JobQueue
from mirrcore.jobs_statistics import JobStatistics
from mirrcore.job_queue_exceptions import JobQueueException
from pika.exceptions import AMQPConnectionError


def is_client_keys_path_configured():
    """
    Return True if CLIENT_KEYS_PATH is set.

    File validity is checked when KeyManager loads.

    Returns
    -------
    Boolean
    """
    path = os.getenv('CLIENT_KEYS_PATH')
    return path is not None and path != ''


class Client:
    """
    The Client class gets a job directly from the job queue.
    It receives a job, performs it depending on the job type.
    A job is performed by calling an api endpoint to request
    a json object. The client saves the result of the job and any included
    attachments using the Saver class.

    Attributes
    ----------
    path_generator : PathGenerator
        Returns a path for the result of a job to be saved to.
    saver : Saver
        Handles the making of directories and the saving of files either
        to disk or Amazon s3.
    redis : redis_server
        Allows for a direct connection to the Redis server, incrementing the
        jobs completed.
    job_queue : JobQueue
        Queue of all of the jobs that need to be completed. The client will
        directly pull jobs from this queue.
    key_manager : KeyManager
        Loads API keys and pacing between calls.
    """
    def __init__(self, redis_server, job_queue, manager):
        self.path_generator = PathGenerator()
        self.saver = Saver(savers=[DiskSaver(),
                                   S3Saver(bucket_name="mirrulations")])
        self.redis = redis_server
        self.job_queue = job_queue
        self.cache = JobStatistics(redis_server)
        self.key_manager = manager

    def _can_connect_to_database(self):
        try:
            self.redis.ping()
        except redis.exceptions.ConnectionError:
            return False
        return True

    def _get_job_from_job_queue(self):
        if not self._can_connect_to_database():
            # temporary, ideally we should get
            # rid of _can_connect_to_database() altogether
            raise NoJobsAvailableException

        if self.job_queue.get_num_jobs() == 0:
            raise NoJobsAvailableException

        job = self.job_queue.get_job()

        return job

    def _set_default_key(self, job, key, default_value):
        if key not in job:
            job[key] = default_value

    def _set_missing_job_key_defaults(self, job):
        self._set_default_key(job, 'job_type', 'other')
        self._set_default_key(job, 'reg_id', 'other_reg_id')
        self._set_default_key(job, 'agency', 'other_agency')
        return job

    def _remove_plural_from_job_type(self, job):
        split_url = str(job['url']).split('/')
        job_type = split_url[-2][:-1]  # Removes plural from job type
        type_id = split_url[-1]
        return f'{job_type}/{type_id}'

    def _get_job(self, key_id: str):
        """
        Get a job from the JobQueue.
        Converts API URL to regulations.gov URL and prints to logs.
        From: https://api.regulations.gov/v4/dockets/type_id
        To: https://www.regulations.gov/docket/type_id

        :raises: NoJobsAvailableException
            If no job is available from the job queue
        """
        job = self._get_job_from_job_queue()

        job = self._set_missing_job_key_defaults(job)

        # update count for dashboard
        self.job_queue.decrement_count(job['job_type'])

        print(f'Job received: {job["job_type"]}'
              + f' (api key id: {key_id})')

        print(f'Regulations.gov link: {job["url"]}')
        print(f'API URL: {job["url"]}')

        return job

    def _download_job(self, job, job_result):
        """
        Downloads the current job and saves the data using the Saver. Downloads
        the attachments if there are any.
        If there are any errors in the job_result, the data json is returned
        as  {'job_id': job_id, 'results': job_result}
        else {
            'job_id': job_id, 'results': job_result,
            'directory': output_path
            }

        Parameters
        ----------
        job : dict
            information about the job being completed
        job_result : dict
            results from a performed job
        """
        data = {
            'job_type': job['job_type'],
            'job_id': job['job_id'],
            'results': job_result,
            'reg_id': job['reg_id'],
            'agency': job['agency']
        }
        print(f'Downloading Job {job["job_id"]}')
        data['directory'] = self.path_generator.get_path(job_result)
        self.cache.increase_jobs_done(data['job_type'])

        self._put_results(data)

        comment_has_attachment = self._does_comment_have_attachment(job_result)
        json_has_file_format = self._document_has_file_formats(job_result)

        if data["job_type"] == "comments" and comment_has_attachment:
            self._download_all_attachments_from_comment(job_result)
        if data["job_type"] == "documents" and json_has_file_format:
            document_htm = self._get_document_htm(job_result)
            if document_htm is not None:
                self._download_htm(job_result)

    def _put_results(self, data):
        """
        Ensures data format matches expected format
        If results are valid, writes them to disk

        Parameters
        ----------
        data : dict
            the results from a performed job
        """
        dir_, filename = data['directory'].rsplit('/', 1)
        self.saver.save_json(f'/data{dir_}/{filename}', data)

    def _perform_job(self, job_url: str, api_cred: KeyCredential):
        """
        Performs job via get_request function by giving it the job_url combined
        with the api_key for validation.

        Parameters
        ----------
        job_url : str
            url from a job
        api_cred : KeyCredential
            Regulations.gov API credential for this request

        Returns
        -------
        dict
            json results of the performed job
        """
        try:
            delimiter = '&' if '?' in job_url else '?'
            url = f'{job_url}{delimiter}api_key={api_cred.api_key}'

            return requests.get(url, timeout=10)
        except requests.exceptions.ReadTimeout as exc:
            raise APITimeoutException from exc

    def _download_all_attachments_from_comment(self, comment_json):
        '''
        Downloads all attachments for a comment

        Parameters
        ----------
        data : dict
            Dictionary of the job
            Keys include: 'job_type', 'job_id', 'results', 'reg_id', 'agency'

        comment_json : dict
            The json of the comment

        '''

        path_list = self.path_generator.get_attachment_json_paths(comment_json)
        counter = 0
        comment_id_str = f"Comment - {comment_json['data']['id']}"
        print(f"Found {len(path_list)} attachment(s) for {comment_id_str}")
        for included in comment_json["included"]:
            if (included["attributes"]["fileFormats"] and
                    included["attributes"]["fileFormats"]
                    not in ["null", None]):
                for attachment in included['attributes']['fileFormats']:
                    url = attachment["fileUrl"]
                    self._download_single_attachment(url,
                                                     path_list[counter])
                    print(f"Downloaded {counter+1}/{len(path_list)} "
                          f"attachment(s) for {comment_id_str}")
                    counter += 1
                    self.cache.increase_jobs_done('attachment',
                                                  url.endswith('.pdf'))

    def _download_single_attachment(self, url, path):
        '''
        Downloads a single attachment for a comment and
        writes it to its correct path

        Parameters
        ----------
        url : str
            The attachment download url
            Ex: http://downloads.regulations.gov/####

        path : str
            The attachment path the download should be written to
            Comes from the path_generator.get_attachment_json_paths

        data : dict
            Dictionary of the job
            Keys include: 'job_type', 'job_id', 'results', 'reg_id', 'agency'

        '''
        response = requests.get(url, timeout=10)
        dir_, filename = path.rsplit('/', 1)
        self.saver.save_binary(f'/data{dir_}/{filename}', response.content)
        filename = path.split('/')[-1]

    def _does_comment_have_attachment(self, comment_json):
        """
        Validates whether a json for a comment has any
        attachments to be downloaded.

        RETURNS
        -------
        True or False depending if there is an attachment
        available to download from a comment
        """
        if "included" in comment_json and len(comment_json["included"]) > 0:
            return True
        return False

    def _download_htm(self, json):
        url = self._get_document_htm(json)
        file_format = self._get_format(json)
        if file_format == "html":
            path = self.path_generator.get_document_html_path(json)
        else:
            path = self.path_generator.get_document_htm_path(json)
        if url is not None:
            response = requests.get(url, timeout=10)
            dir_, filename = path.rsplit('/', 1)
            self.saver.save_binary(f'/data{dir_}/{filename}', response.content)
        print(f"SAVED document HTM - {url} to path: ", path)
        self.cache.increase_jobs_done('attachment')

    def _get_format(self, json):
        file_formats = json["data"]["attributes"]["fileFormats"]
        for file_format in file_formats:
            if file_format.get("format") in ("htm", "html"):
                return file_format.get("format")
        return "htm"

    def _get_document_htm(self, json):
        """
        Gets the download link for a documents HTM if one exists

        RETURNS
        -------
        A download link to a documents HTM
        """
        file_formats = json["data"]["attributes"]["fileFormats"]
        for file_format in file_formats:
            if file_format.get("format") in ("htm", "html"):
                file_url = file_format.get("fileUrl")
                if file_url is not None:
                    return file_url
        return None

    def _document_has_file_formats(self, json):
        """
        Checks to see if the necessary attribute of fileFormats
        exists

        RETURNS
        -------
        true if the necessary attribute exists
        """
        if "data" not in json or "attributes" not in \
            json["data"] or "fileFormats" not in \
                json["data"]["attributes"]:
            return False
        if json["data"]["attributes"]["fileFormats"] is None:
            return False
        return True

    def job_operation(self, api_cred: KeyCredential):
        """
        Processes a job.
        The Client gets the job from the job queue, performs the job
        based on job_type, then saves the job results using the saver class.

        Parameters
        ----------
        api_cred : KeyCredential
            API credential to use for this job's Regulations.gov request.
        """
        job = self._get_job(api_cred.id)

        try:
            response = self._perform_job(job['url'], api_cred)
            response.raise_for_status()
            result = response.json()

            self._download_job(job, result)
        except Exception:
            print(
                f'FAILURE: bad job job_id={job["job_id"]} url={job["url"]}',
                flush=True)
            raise

        return job


if __name__ == '__main__':
    load_dotenv()
    if not is_client_keys_path_configured():
        print('Need CLIENT_KEYS_PATH environment variable.')
        sys.exit(1)

    keys_path = os.environ['CLIENT_KEYS_PATH']
    try:
        key_manager = KeyManager(keys_path)
    except (KeyManagerFileError, KeyManagerJsonError) as exc:
        print(f'Could not load API keys file: {exc}')
        sys.exit(1)

    try:
        redis_client = load_redis()
    except redis.exceptions.ConnectionError:
        print('There is no Redis database to connect to.')
        sys.exit(1)
    client = Client(redis_client, JobQueue(redis_client), key_manager)

    while True:
        try:
            cred = key_manager.get_next()
            job_ = client.job_operation(cred)
            print(f'SUCCESS: {job_["url"]} complete.')
        except redis.exceptions.ConnectionError:
            print('FAILURE: Could not connect to Redis.')
        except NoJobsAvailableException:
            pass
        except APITimeoutException:
            print('FAILURE: Request to API timed out.')
        except requests.exceptions.HTTPError as err:
            print(f"FAILURE: HTTP error\
                  {err.response.status_code} occurred: {err}")
        except JobQueueException:
            print("The Job Queue is down.")
        except AMQPConnectionError:
            print("RabbitMQ is still loading")

        time.sleep(key_manager.seconds_between_api_calls())
