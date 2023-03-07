# pylint: disable=too-many-locals
import time
import os
import sys
from base64 import b64encode
from json import dumps, loads
import requests
from dotenv import load_dotenv
from mirrcore.attachment_saver import AttachmentSaver


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
    print(f'Job output path: {output_path}')

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
            and os.getenv('API_KEY') is not None
            and os.getenv('ID') is not None)


class Client:
    """
    The Client class performs jobs given to it by a workserver
    It receives a job, performs it depending on the job type.
    A job is performed by calling an api endpoint to request
    a json object. The Client sends back the results back
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
        self.client_id = os.getenv('ID')

        hostname = os.getenv('WORK_SERVER_HOSTNAME')
        port = os.getenv('WORK_SERVER_PORT')
        self.url = f'http://{hostname}:{port}'

    def get_job(self):
        """
        Get a job from the work server.
        Converts API URL to regulations.gov URL and prints to logs.
        From: https://api.regulations.gov/v4/dockets/type_id
        To: https://www.regulations.gov/docket/type_id

        :raises: NoJobsAvailableException
            If no job is available from the work server
        """

        response = requests.get(f'{self.url}/get_job',
                                params={'client_id': self.client_id},
                                timeout=10)

        job = loads(response.text)
        link = 'https://www.regulations.gov/'
        if 'error' in job:
            raise NoJobsAvailableException()
        split_url = str(job['url']).split('/')
        job_type = split_url[-2][:-1]  # Removes plural from job type
        type_id = split_url[-1]
        print(f'Regulations.gov link: {link}{job_type}/{type_id}')
        print(f'API URL: {job["url"]}')
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
        print(f'Sending Job {job["job_id"]} to Work Server')
        # If the job is not an attachment job we need to add an output path
        if ('errors' not in job_result) and (job['job_type'] != 'attachments'):
            data['directory'] = get_output_path(job_result)
        requests.put(f'{self.url}/put_results', json=dumps(data),
                     params={'client_id': self.client_id},
                     timeout=10)
        self._handle_results(data)

        # For now, still need to send original put request for Mongo
        # requests.put(
        #     f'{self.url}/put_results',
        #     json=dumps(data['job_id']),
        #     params={'client_id': self.client_id},
        #     timeout=10
        # )

    def _handle_results(self, data):
        """
        Verifies job results and deals with them appropriately.

        Parameters
        ----------
        data : dict
            the results from a performed job
        """
        if not data or not data.get('results'):
            print(f'{data.get("job_id")}: No results found')
            return
        if data.get('job_type', '') == 'attachments':
            self._put_attachment_results(data)
        else:
            self._put_results(data)

    def _put_attachment_results(self, data):
        """
        Ensures data format matches what is expected for attachments
        If results are valid, writes them to disk

        Parameters
        ----------
        data : dict
            the results from a performed job
        """
        print("Attachment Job Being Saved")
        if any(x in data['results'] for x in ['error', 'errors']):
            print(f"{data['job_id']}: Errors found in results")
            return
        print(f"agency: {data['agency']}")
        print(f"reg_id: {data['reg_id']}")
        AttachmentSaver().save(
            data,
            f"/data/{data['agency']}/{data['reg_id']}"
        )
        print(f"/data/{data['agency']}/{data['reg_id']}")
        print(f"{data['job_id']}: Attachment result(s) written to disk")

    def _put_results(self, data):
        """
        Ensures data format matches expected format
        If results are valid, writes them to disk

        Parameters
        ----------
        data : dict
            the results from a performed job
        """
        if any(x in data['results'] for x in ['error', 'errors']):
            print(f"{data['job_id']}: Errors found in results")
            return
        if not data.get('directory') or data.get('directory').rfind('/') == -1:
            print(f"{data['job_id']}: \
                  No directory found in results or was incorrect")
            return
        self._write_results(data)
        print(f"{data['job_id']}: Results written to disk")

    def _write_results(self, data):
        """
        writes the results to disk. used by docket document and comment jobs

        Parameters
        ----------
        data : dict
            the results data to be written to disk
        """
        dir_, filename = data['directory'].rsplit('/', 1)
        try:
            os.makedirs(f'/data/{dir_}')
        except FileExistsError:
            print(f'Directory already exists in root: /data/{dir_}')
        with open(f'/data/{dir_}/{filename}', 'w+', encoding='utf8') as file:
            print('Writing results to disk')
            file.write(dumps(data['results']))

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
        print('Performing job')
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
        response_json = requests.get(
            f"{url}?api_key={self.api_key}",
            timeout=10
        ).json()

        if any(x in response_json for x in ('error', 'errors')):
            return response_json

        if not self.does_attachment_exists(response_json):
            print(f"No attachments to download from {url}")
            return {}

        # Get Attachments
        print(f"Performing attachment job {url}")
        file_info = \
            response_json["data"][0]["attributes"]["fileFormats"]
        file_urls, file_types = get_urls_and_formats(file_info)
        return self.download_attachments(file_urls, file_types, job_id)

    def does_attachment_exists(self, attachment_json):
        """
        Validates whether a json for an attachment is valid to continue
        download process. Invalid JSON means no attachment(s) available

        RETURNS
        -------
        True or False depending if there is an attachment available to download
        """
        # handle KeyError & IndexError
        if not attachment_json.get('data', []):
            return False
        data = attachment_json['data'][0]

        # Check if attributes and fileFormats exists
        if not data.get('attributes', {}).get('fileFormats'):
            return False

        return True

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
        print('Downloading attachments')
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
        print('Processing job from work server')
        job = self.get_job()
        if job['job_type'] == 'attachments':
            result = self.perform_attachment_job(job['url'], job['job_id'])
        else:
            result = self.perform_job(job['url'])
        self.send_job(job, result)
        if any(x in result for x in ('error', 'errors')):
            print(f'FAILURE: Error in {job["url"]}')
        else:
            print(f'SUCCESS: {job["url"]} complete')


if __name__ == '__main__':
    load_dotenv()
    if not is_environment_variables_present():
        print('Need client environment variables')
        sys.exit(1)

    client = Client()

    while True:
        try:
            client.job_operation()
        except NoJobsAvailableException:
            print("No Jobs Available")
        time.sleep(3.6)
