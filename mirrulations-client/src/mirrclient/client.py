# pylint: disable=too-many-locals
import time
import os
import sys
from base64 import b64encode
from json import dumps, loads
import requests
import boto3
from dotenv import load_dotenv


class NoJobsAvailableException(Exception):
    """
    Raises an Exception when there are no jobs available in the workserver.
    """

    def __init__(self, message="There are no jobs available"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


def get_urls_and_formats(file_info):
    """
    Parameters
    ----------
    file_info : dict
        a json of file formats and urls

    Returns
    -------
    two lists of urls and file formats
    """
    urls = []
    formats = []

    for link in file_info:
        urls.append(link["fileUrl"])
        formats.append(link["format"])

    return urls, formats


def get_key_path_string(results, key):
    """
    Creates path for keys in results

    Parameters
    ----------
    results : dict
        The results of a performed job

    key : str
        A key in the result
    """
    if key in results.keys():
        if results[key] is None:
            return 'None/'
        return results[key] + "/"
    return ""


def get_output_path(results):
    """
    Takes results from a performed job and creates an output
    path for a directory.

    Parameters
    ----------
    results : dict
        the results from a performed job

    Returns
    -------
    str
        the output path for the job
    """
    if 'error' in results:
        return -1
    output_path = ""
    data = results["data"]["attributes"]
    output_path += get_key_path_string(data, "agencyId")
    output_path += get_key_path_string(data, "docketId")
    output_path += get_key_path_string(data, "commentOnDocumentId")
    output_path += results["data"]["id"] + "/"
    output_path += results["data"]["id"] + ".json"
    return output_path


def is_environment_variables_present():
    """
    A boolean function that returns whether environment variables are
    present for performing jobs.

    Returns
    -------
    Boolean
    """
    return (os.getenv('WORK_SERVER_HOSTNAME') is not None
            and os.getenv('WORK_SERVER_PORT') is not None
            and os.getenv('API_KEY') is not None)


# Credientals folder is still missing such as ~/.aws/credentials
def check_for_s3_connection():
    """
    Checks if a valid connection could be made to s3
    """
    try:
        session = boto3.Session(profile_name="profile_name")
        s3 = session.client("s3")
        connection = s3.listBuckets()
        if connection["ResponseMetaData"]["HTTPStatusCode"] == 200:
            return True
        else:
            return False
    except Exception as exception:
        return False 


# profile_name is located in the credentials folder
def put_results_s3(data, bucket_name, file_name):
    """
    Puts the results in an s3 bucket.
    Parameters
    ----------
    data : dict
        the data to be stored
    bucket_name : str
        name of the bucket
    file_name : str
        the file name to write to
    """
    session = boto3.Session(profile_name="profile_name")
    s3 = session.client("s3")
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=data)


class Client:
    """
    The Client class performs jobs given to it by a workserver
    It recieves a job, performs it depending on the job type.
    A job is performed by calling an api endpoint to request
    a json obect. The Client sends back the results back
    to the workserver.

    Attributes
    ----------
    api_key : str
        Api key used to authenticate requests made to api
    server_validator : ServerValidator
        This is used to validate requests made between the
        workserver and the Client
    client_id : int
        An id that defaults to -1 but is eventually replaced by a
        value from the workserver.
    """

    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.client_id = -1

        hostname = os.getenv('WORK_SERVER_HOSTNAME')
        port = os.getenv('WORK_SERVER_PORT')
        self.url = f'http://{hostname}:{port}'

    def get_id(self):
        """
        Retrieves an id for the Client from the workserver.
        That value is saved to client_id then written to
        a client.cfg file.
        """
        response = requests.get(f'{self.url}/get_client_id', timeout=10)
        self.client_id = int(response.json()['client_id'])
        with open('client.cfg', 'w', encoding='utf8') as file:
            file.write(str(self.client_id))

    def get_job(self):
        """
        Get a job from the work server.

        :raises: NoJobsAvailableException
            If no job is available from the work server
        """
        print('performing job')

        response = requests.get(f'{self.url}/get_job',
                                params={'client_id': self.client_id},
                                timeout=10)

        job = loads(response.text)
        if 'error' in job:
            raise NoJobsAvailableException()

        return job

    def send_job(self, job, job_result):
        """
        Returns the job results to the workserver
        If there are any errors in the job_result, the data json is returned
        as  {'job_id': job_id, 'results': job_result}
        else {
            'job_id': job_id, 'results': job_result,
            'directory': output_path
            }

        Parameters
        ----------
        job_id : str
            id for current job
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
        # If the job is not an attachment job we need to add an output path
        if ('errors' not in job_result) and (job['job_type'] != 'attachments'):
            data['directory'] = get_output_path(job_result)
        requests.put(f'{self.url}/put_results', json=dumps(data),
                     params={'client_id': self.client_id},
                     timeout=10)

    def perform_job(self, job_url):
        """
        Performs job via get_request function by giving it the job_url combined
        with the Client api_key for validation.

        Parameters
        ----------
        job_url : str
            url from a job

        Returns
        -------
        dict
            json results of the performed job
        """
        return requests.get(job_url + f'?api_key={self.api_key}',
                            timeout=10).json()

    def perform_attachment_job(self, url, job_id):
        """
        Performs an attachment job via get_request function by giving
        it the job_url combined with the Client api_key for validation.

        The attachments are encoded and saved to a dictionary. The name is
        created from the job_id and the file extension is the same as the
        file type.

        The files are encoded in order to send them to the workserver
        as part of a json.

        Parameters
        ----------
        url : str
            url from a job

        api_key : str
            api_key for the client

        job_id : str
            id of the job

        Returns
        -------
        a dict of encoded files
        """
        url = url + f'?api_key={self.api_key}'
        response_from_related = requests.get(url, timeout=10).json()

        # Get attachments
        try:
            file_urls, file_types = \
                get_urls_and_formats(
                    response_from_related["data"][0]
                    ["attributes"]["fileFormats"])
        except IndexError:
            return {}
        return self.download_attachments(file_urls, file_types, job_id)

    def download_attachments(self, urls, file_types, job_id):
        """
        Downloads attachments from regulations.gov.

        Parameters
        ----------
        urls : list of str
            urls of attachments

        file_types : list of str
            file formats of attachments

        job_id : str
            id of the job

        Returns
        -------
        a dict of encoded files
        """
        attachments = {}
        for i, (url, file_type) in enumerate(zip(urls, file_types)):
            attachment = requests.get(url, timeout=10)
            attachments[f'{job_id}_{i}.{file_type}'] = b64encode(
                attachment.content).decode('ascii')
        return attachments

    def job_operation(self):
        """
        Processes a job.
        The Client gets the job from the workserver, performs the job
        based on job_type, then sends back the job results to
        the workserver.
        """
        job = self.get_job()
        if job['job_type'] == 'attachments':
            result = self.perform_attachment_job(job['url'], job['job_id'])
        else:
            result = self.perform_job(job['url'])
        self.send_job(job, result)


if __name__ == '__main__':
    load_dotenv()
    if not is_environment_variables_present():
        print('Need client environment variables')
        sys.exit(1)

    client = Client()
    client.get_id()

    print('Your ID is: ', client.client_id)
    while True:
        try:
            client.job_operation()
        except NoJobsAvailableException:
            print("No Jobs Available")
        time.sleep(3.6)
