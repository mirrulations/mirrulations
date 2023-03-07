import os
import json
from mirrcore.attachment_saver import AttachmentSaver
import pytest
from pytest import fixture, raises
import requests_mock
from mirrclient.client import NoJobsAvailableException, Client
from mirrclient.client import is_environment_variables_present
from mirrclient.client import get_output_path
from requests.exceptions import Timeout

BASE_URL = 'http://work_server:8080'


@fixture(autouse=True)
def mock_env():
    os.environ['WORK_SERVER_HOSTNAME'] = 'work_server'
    os.environ['WORK_SERVER_PORT'] = '8080'
    os.environ['API_KEY'] = 'TESTING_KEY'
    os.environ['ID'] = '-1'


@fixture(name='mock_requests')
def fixture_mock_requests():
    return requests_mock.Mocker()


@fixture(autouse=True)
def mock_disk_writing(mocker):
    """
    Mock tests that would be writing to disk
    """
    # patch _write_results and AttachmentSaver.save
    mocker.patch.object(
        Client,
        '_write_results',
        return_value=None
    )
    mocker.patch.object(
        AttachmentSaver,
        'save',
        return_value=None
    )


def test_check_no_env_values():
    # Need to delete env variables set by mock_env fixture
    del os.environ['WORK_SERVER_HOSTNAME']
    del os.environ['WORK_SERVER_PORT']
    del os.environ['API_KEY']
    assert is_environment_variables_present() is False


def test_check_no_hostname():
    # Need to delete hostname env variable set by mock_env fixture
    del os.environ['WORK_SERVER_HOSTNAME']
    assert is_environment_variables_present() is False


def test_check_no_server_port():
    # Need to delete server port env variable set by mock_env fixture
    del os.environ['WORK_SERVER_PORT']
    assert is_environment_variables_present() is False


def test_check_no_api_key():
    # Need to delete api key env variable set by mock_env fixture
    del os.environ['API_KEY']
    assert is_environment_variables_present() is False


def test_client_has_no_id():
    # Need to delete id env variable set by mock_env fixture
    del os.environ['ID']
    assert is_environment_variables_present() is False


def test_client_gets_job(mock_requests):
    client = Client()
    link = 'https://api.regulations.gov/v4/type/type_id'
    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1', 'url': link, 'job_type': 'attachments',
                  'reg_id': '1', 'agency': 'foo'},
            status_code=200
        )
        job_info = client.get_job()
        assert {'job_id': '1',
                'url': link,
                'job_type': 'attachments',
                'reg_id': '1',
                'agency': 'foo'} == job_info


def test_client_throws_exception_when_no_jobs(mock_requests):
    client = Client()
    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'error': 'No jobs available'},
            status_code=403
        )

        with raises(NoJobsAvailableException):
            client.get_job()


def test_api_call_has_api_key(mock_requests):
    client = Client()
    client.api_key = 'KEY12345'
    with mock_requests:
        mock_requests.get(
            'http://regulations.gov/job',
            json={'data': {'foo': 'bar'}},
            status_code=200
        )
        client.perform_job('http://regulations.gov/job')

        assert '?api_key=KEY12345' in mock_requests.request_history[0].url


def test_client_performs_job(mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'documents',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://url.com?api_key=1234',
            json={'data': {'id': '1', 'attributes': {'agencyId': 'NOAA'},
                           'job_type': 'documents'}},
            status_code=200
        )
        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

        put_request = mock_requests.request_history[2]
        json_data = json.loads(put_request.json())
        saved_data = json_data['results']['data']
        assert saved_data['attributes'] == {'agencyId': 'NOAA'}
        assert saved_data['id'] == '1'
        assert saved_data['job_type'] == 'documents'


def test_client_returns_403_error_to_server(mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'documents',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )

        regulation_response = {"errors": [{
            "status": "403",
            "title": "The document ID could not be found."}],
            "error": "API limit reached."
        }

        mock_requests.get(
            'http://url.com?api_key=1234',
            json=regulation_response,
            status_code=403
        )

        mock_requests.put(
            'http://work_server:8080/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )
        client.job_operation()
        response = mock_requests.request_history[-1]
        assert '403' in response.json()


def test_get_job_timesout(mock_requests):
    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job',
            exc=Timeout)

        with pytest.raises(Timeout):
            Client().get_job()


def test_perform_job_timesout(mock_requests):
    with mock_requests:
        fake_url = 'http://regulations.gov/fake/api/call'
        mock_requests.get(
            fake_url,
            exc=Timeout)

        with pytest.raises(Timeout):
            Client().perform_job(fake_url)


def test_perform_attachment_job_timesout(mock_requests):
    with mock_requests:
        fake_url = 'http://regulations.gov/fake/api/call'
        mock_requests.get(
            fake_url,
            exc=Timeout)

        with pytest.raises(Timeout):
            fake_job_id = 'fake'
            Client().perform_attachment_job(fake_url, fake_job_id)


def test_download_attachments_times_out(mock_requests):
    with mock_requests:
        fake_url = 'http://regulations.gov/fake/api/call'
        mock_requests.get(
            fake_url,
            exc=Timeout)

        with pytest.raises(Timeout):
            fake_job_id = 'fake'
            fake_attachment_types = ['pdf']
            Client().download_attachments([fake_url],
                                          fake_attachment_types,
                                          fake_job_id)


def test_client_returns_400_error_to_server(mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'documents',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )

        regulation_response = {"errors": [{
            "status": "400",
            "title": "The document ID could not be found."}]}

        mock_requests.get(
            'http://url.com?api_key=1234',
            json=regulation_response,
            status_code=400
        )

        mock_requests.put(
            'http://work_server:8080/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )
        client.job_operation()
        response = mock_requests.request_history[-1]
        assert '400' in response.json()


def test_client_returns_500_error_to_server(mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'documents',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )

        regulation_response = {"errors": [{
            "status": "500",
            "title": "INTERNAL_SERVER_ERROR",
            "detail": "Incorrect result size: expected 1, actual 2"}]
        }

        mock_requests.get(
            'http://url.com?api_key=1234',
            json=regulation_response,
            status_code=500
        )

        mock_requests.put(
            'http://work_server:8080/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )
        client.job_operation()
        response = mock_requests.request_history[-1]
        assert '500' in response.json()


def test_client_sends_attachment_results(mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'attachments',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://url.com?api_key=1234',
            json={"data": [{"id": "0900006480cb703d", "type": "attachments",
                           "attributes": {"fileFormats": [
                               {"fileUrl": "https://downloads.regulations.gov",
                                "format": "doc"}]}}]
                  },
            status_code=200
        )

        mock_requests.get(
            "https://downloads.regulations.gov",
            json={"data": 'foobar'},
            status_code=200
        )
        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

        mock_requests.put(f'{BASE_URL}/put_results', text='{}')
        client.job_operation()
        put_request = mock_requests.request_history[3]
        json_data = json.loads(put_request.json())
        assert json_data['job_id'] == "1"
        assert json_data['job_type'] == "attachments"
        assert json_data['results'] == {'1_0.doc': 'eyJkYXRhIjogImZvb2JhciJ9'}


def test_client_handles_empty_json_from_regulations(mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'attachments',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://url.com?api_key=1234',
            json={"data": []
                  },
            status_code=200
        )

        mock_requests.get(
            "https://downloads.regulations.gov",
            json={"data": 'foobar'},
            status_code=200
        )
        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

        mock_requests.put(f'{BASE_URL}/put_results', text='{}')
        client.job_operation()
        put_request = mock_requests.request_history[2]
        json_data = json.loads(put_request.json())
        assert json_data['job_id'] == "1"
        assert json_data['job_type'] == "attachments"
        assert json_data['results'] == {}


def test_get_output_path_error():
    results = {'error': 'error'}
    output_path = get_output_path(results)

    assert output_path == -1


def test_handles_nonetype_error(mock_requests):
    """
    Test for handling of the NoneType Error caused by null fileformats
    """
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://regulations.gov/job',
                  'job_type': 'attachments',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://regulations.gov/job?api_key=1234',
            json={
                "data": [{
                    "attributes": {
                        "fileFormats": None,
                    }
                }]
            },
            status_code=200
        )

        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()
        put_request = mock_requests.request_history[2]
        json_data = json.loads(put_request.json())
        assert json_data['job_type'] == "attachments"
        assert json_data['results'] == {}


def test_handles_index_error(mock_requests):
    """
    Test that handles IndexError as a result of an attachment json being:
    {
        'data' = []
    }
    """
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://regulations.gov/job',
                  'job_type': 'attachments',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://regulations.gov/job?api_key=1234',
            json={"data": []},
            status_code=200
        )

        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()
        put_request = mock_requests.request_history[2]
        json_data = json.loads(put_request.json())
        assert json_data['job_type'] == "attachments"
        assert json_data['results'] == {}


def test_success_client_logging(capsys, mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'https://api.regulations.gov/v4/documents/type_id',
                  'job_type': 'documents',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'https://api.regulations.gov/v4/documents/type_id?api_key=1234',
            json={'data': {'id': '1', 'attributes': {'agencyId': 'NOAA'},
                           'job_type': 'documents'}},
            status_code=200
        )
        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

    captured = capsys.readouterr()
    print_data = [
        'Processing job from work server\n',
        'Regulations.gov link: https://www.regulations.gov/document/type_id\n',
        'API URL: https://api.regulations.gov/v4/documents/type_id\n',
        'Performing job\n',
        'Sending Job 1 to Work Server\n',
        'Job output path: NOAA/1/1.json\n',
        '1: Results written to disk\n',
        'SUCCESS: https://api.regulations.gov/v4/documents/type_id complete\n'
    ]
    assert captured.out == "".join(print_data)


def test_success_attachment_logging(capsys, mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'attachments',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://url.com?api_key=1234',
            json={"data": [{"id": "0900006480cb703d", "type": "attachments",
                           "attributes": {"fileFormats": [
                               {"fileUrl": "https://downloads.regulations.gov",
                                "format": "doc"}]}}]
                  },
            status_code=200
        )

        mock_requests.get(
            "https://downloads.regulations.gov",
            json={"data": 'foobar'},
            status_code=200
        )
        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

        print_data = {
            'Processing job from work server\n'
            'Regulations.gov link: https://www.regulations.gov//url.com\n'
            'API URL: http://url.com\n'
            'Performing attachment job http://url.com\n'
            'Downloading attachments\n'
            'Sending Job 1 to Work Server\n'
            'Attachment Job Being Saved\n'
            'agency: foo\n'
            'reg_id: 1\n'
            '/data/foo/1\n'
            '1: Attachment result(s) written to disk\n'
            'SUCCESS: http://url.com complete\n'
        }

        captured = capsys.readouterr()
        assert captured.out == "".join(print_data)


def test_success_no_attachment_logging(capsys, mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'attachments',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://url.com?api_key=1234',
            json={"data": []},
            status_code=200
        )

        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

        print_data = {
            'Processing job from work server\n'
            'Regulations.gov link: https://www.regulations.gov//url.com\n'
            'API URL: http://url.com\n'
            'No attachments to download from http://url.com\n'
            'Sending Job 1 to Work Server\n'
            '1: No results found\n'
            'SUCCESS: http://url.com complete\n'
        }

        captured = capsys.readouterr()
        assert captured.out == "".join(print_data)


def test_failure_job_results(capsys, mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'documents',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://url.com?api_key=1234',
            json={"error": 'foobar'},
            status_code=200
        )
        mock_requests.get(
            "https://downloads.regulations.gov",
            json={"error": 'foobar'},
            status_code=200
        )
        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

        print_data = {
            'Processing job from work server\n'
            'Regulations.gov link: https://www.regulations.gov//url.com\n'
            'API URL: http://url.com\n'
            'Performing job\n'
            'Sending Job 1 to Work Server\n'
            '1: Errors found in results\n'
            'FAILURE: Error in http://url.com\n'
        }

        captured = capsys.readouterr()
        assert captured.out == "".join(print_data)


def test_failure_attachment_job_results(capsys, mock_requests):
    client = Client()
    client.api_key = 1234

    with mock_requests:
        mock_requests.get(
            'http://work_server:8080/get_job?client_id=-1',
            json={'job_id': '1',
                  'url': 'http://url.com',
                  'job_type': 'attachments',
                  'reg_id': '1',
                  'agency': 'foo'},
            status_code=200
        )
        mock_requests.get(
            'http://url.com?api_key=1234',
            json={"error": 'foobar'},
            status_code=200
        )
        mock_requests.get(
            "https://downloads.regulations.gov",
            json={"error": 'foobar'},
            status_code=200
        )
        mock_requests.put('http://work_server:8080/put_results', text='{}')
        client.job_operation()

        print_data = {
            'Processing job from work server\n'
            'Regulations.gov link: https://www.regulations.gov//url.com\n'
            'API URL: http://url.com\n'
            'Sending Job 1 to Work Server\n'
            'Attachment Job Being Saved\n'
            '1: Errors found in results\n'
            'FAILURE: Error in http://url.com\n'
        }

        captured = capsys.readouterr()
        assert captured.out == "".join(print_data)
