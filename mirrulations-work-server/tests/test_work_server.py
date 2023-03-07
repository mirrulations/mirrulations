from json import dumps
import base64
from pytest import fixture
from mirrserver.work_server import create_server
from mirrmock.mock_flask_server import mock_work_server


@fixture(name='mock_server')
def fixture_mock_server():
    return mock_work_server(create_server)


def test_create_mock_database(mock_server):
    assert mock_server.redis is not None


def test_create_mock_server(mock_server):
    assert mock_server.app is not None


def test_new_mock_database_is_empty(mock_server):
    assert mock_server.redis.keys() == []


def test_data_entry_in_mock_database_is_correct(mock_server):
    mock_server.redis.set('val1', 1)
    assert mock_server.redis.get('val1').decode() == '1'


def test_data_entry_changes_in_mock_database(mock_server):
    mock_server.redis.set('val1', 1)
    mock_server.redis.set('val1', 2)
    assert mock_server.redis.get('val1').decode() != '1'
    assert mock_server.redis.get('val1').decode() == '2'


def test_data_deleted_from_mock_database_is_gone(mock_server):
    mock_server.redis.set('val1', 1)
    assert mock_server.redis.get('val1').decode() == '1'
    mock_server.redis.delete('val1')
    assert mock_server.redis.get('val1') is None


def test_get_job_without_client_id_is_unauthorized(mock_server):
    response = mock_server.client.get('/get_job')
    assert response.status_code == 401
    expected = {'error': 'Client ID was not provided'}
    assert response.get_json() == expected


def test_get_job_has_no_available_job(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    params = {'client_id': 1}
    response = mock_server.client.get('/get_job', query_string=params)
    assert response.status_code == 403
    expected = {'error': 'No jobs available'}
    assert response.get_json() == expected


def test_get_job_returns_single_job(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    params = {'client_id': 1}
    job = {'job_id': 1,
           'url': 'url',
           'job_type': 'docket',
           'reg_id': 3,
           'agency': 'EPA'}
    mock_server.redis.rpush('jobs_waiting_queue', dumps(job))
    response = mock_server.client.get('/get_job', query_string=params)
    assert response.status_code == 200
    expected = {'job_id': '1',
                'url': 'url',
                'job_type': 'docket',
                'reg_id': 3,
                'agency': 'EPA'}
    assert response.get_json() == expected


def test_get_waiting_job_is_now_in_progress_and_not_waiting(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    params = {'client_id': 1}
    job = {'job_id': 3, 'url': 'url'}
    mock_server.redis.rpush('jobs_waiting_queue', dumps(job))
    mock_server.client.get('/get_job', query_string=params)
    assert mock_server.redis.llen('jobs_waiting_queue') == 0
    keys = mock_server.redis.hkeys('jobs_in_progress')
    assert mock_server.redis.hget('jobs_in_progress',
                                  keys[0]).decode() == 'url'


def test_put_results_message_body_contains_no_results(mock_server):
    response = mock_server.client.put('/put_results', json=dumps({}))
    assert response.status_code == 403
    assert response.json['error'] == 'The body does not contain the results'


def test_put_results_with_zero_jobs_in_progress(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    mock_server.redis.hset('jobs_in_progress', 2, '')
    data = dumps({'results': {'': ''}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert mock_server.redis.hget('jobs_in_progress', 2).decode() == ''
    assert response.status_code == 403


def test_put_results_returns_directory_error(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    data = dumps({'results': {'': ''}, 'directory': None})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 403
    expected = {'error': 'No directory was included or was incorrect'}
    assert response.get_json() == expected


def test_put_results_without_client_id(mock_server):
    data = dumps({'results': {'': ''}, 'directory': None})
    response = mock_server.client.put('/put_results', json=data)
    assert response.get_json() == {'error': 'Client ID was not provided'}


def test_put_results_with_non_numerical_client_id(mock_server):
    data = dumps({'results': {'': ''}, 'directory': None})
    params = {'client_id': 'a'}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 401
    assert response.get_json() == {'error': 'Invalid client ID'}


def test_client_attempts_to_put_job_that_it_did_not_get(mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 2)
    mock_server.redis.set('total_num_client_ids', 2)
    data = dumps({'job_id': 2, 'directory': 'dir/dir',
                  'results': {2: 3}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 403
    expected = {'error': 'The client ID was incorrect'}
    assert response.get_json() == expected


def test_client_attempts_to_put_job_that_does_not_exist(mock_server):
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({'job_id': 2, 'directory': 'dir/dir',
                  'results': {2: 3}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 403
    expected = {'error': 'The job being completed was not in progress'}
    assert response.get_json() == expected


# def test_put_resuts_no_database(mock_server, mocker):

#     mock_write_results(mocker)
#     mock_server.redis.hset('jobs_in_progress', 2, 3)
#     mock_server.redis.hset('client_jobs', 2, 1)
#     mock_server.redis.set('total_num_client_ids', 1)

#     data = dumps({'job_id': 2, 'results': {"errors": [{
#         "status": "500",
#         "title": "INTERNAL_SERVER_ERROR",
#         "detail": "Cannot connect to the database"}]}})

#     params = {'client_id': 1}
#     mock_server.redis_server.connected = False
#     response = mock_server.client.put('/put_results',
#                                       json=data, query_string=params)
#     assert response.status_code == 500
#     # Not sure this is the best way to do this...
#     expected = {'error': 'Cannot connect to the database'}
#     assert response.get_json() == expected


def test_put_results_returns_correct_job(mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({'job_id': 2, 'directory': 'dir/dir', 'job_type': 'dockets',
                  'results': {'data': {
                      'type': 'dockets'
                  }}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    expected = {'success': 'Job was successfully completed'}
    assert response.get_json() == expected
    assert len(mock_server.data.added) == 1


def test_put_results_returns_correct_attachment_job(mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)
    with open('mirrulations-core/tests/test_files/test.pdf', 'rb') as file:
        data = dumps({'job_id': 2,
                      'job_type': 'attachments',
                      'agency': 'EPA',
                      'reg_id': 'AAAAA',
                      'results': {'1234_0': base64.b64encode(
                        file.read()).decode('ascii')}})
        params = {'client_id': 1}
        response = mock_server.client.put('/put_results',
                                          json=data, query_string=params)
    expected = {'success': 'Job was successfully completed'}
    assert response.get_json() == expected
    assert response.status_code == 200
    assert len(mock_server.data.attachments_added) == 1


def test_put_results_correct_attachment_job_no_files(mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({'job_id': 2,
                  'job_type': 'attachments',
                  'results': {},
                  'reg_id': 'AAAA',
                  'agency': 'EPA'})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    expected = {'success': 'Job completed no attachments'}
    assert response.get_json() == expected
    assert response.status_code == 200
    assert len(mock_server.data.attachments_added) == 0


def test_client_id_not_digit(mock_server):
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({'job_id': 2, 'directory': 'dir/dir',
                  'results': {2: 3}})
    params = {'client_id': 'a'}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 401
    assert response.get_json() == {'error': 'Invalid client ID'}


def test_put_results_returns_500_error_from_regulations(mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)

    data = dumps({'job_id': 2, 'results': {"errors": [{
        "status": "500",
        "title": "INTERNAL_SERVER_ERROR",
        "detail": "Incorrect result size: expected 1, actual 2"}]}})

    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    # Not sure this is the best way to do this...
    expected = {'success': 'Job was successfully completed'}
    assert response.get_json() == expected

    assert mock_server.redis.hlen('invalid_jobs') == 1
    assert mock_server.redis.hlen('jobs_done') == 0
    assert mock_server.redis.hlen('jobs_in_progress') == 0


def test_put_results_returns_404_error_from_regulations(mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)

    data = dumps({'job_id': 2, 'results': {"errors": [{
        "status": "404",
        "title": "The document ID could not be found."}]}})

    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    # Not sure this is the best way to do this...
    expected = {'success': 'Job was successfully completed'}
    assert response.get_json() == expected

    assert mock_server.redis.hlen('invalid_jobs') == 1
    assert mock_server.redis.hlen('jobs_done') == 0
    assert mock_server.redis.hlen('jobs_in_progress') == 0


def test_server_handles_client_error_to_access_api_endpoint(mock_server):
    mock_server.redis.set('total_num_client_ids', 1)
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    data = dumps({'job_id': 2, 'directory': -1,
                  'results': {'error': 'Endpoint not found'}})
    params = {'client_id': 1}
    mock_server.client.put('/put_results', json=data, query_string=params)
    invalid_jobs = mock_server.redis.hkeys('invalid_jobs')
    assert len(invalid_jobs) == 1


def test_database_returns_error_when_database_does_not_exist(mock_server):
    params = {'client_id': 1}
    mock_server.redis_server.connected = False
    response = mock_server.client.get('/get_job', query_string=params)
    assert response.json['error'] == 'Cannot connect to the database'
    assert response.status_code == 500


def test_get_newer_jobs_from_job_waiting_queue(mock_server):
    params = {'client_id': 1}
    for i in range(2):
        mock_server.redis.incr('total_num_client_ids')
        job = {'job_id': i,
               'url': 'url',
               'job_type': 'docket',
               'reg_id': 3,
               'agency': 'EPA'
               }
        mock_server.redis.lpush('jobs_waiting_queue', dumps(job))
    for i in range(2):
        response = mock_server.client.get('/get_job', query_string=params)
        assert response.status_code == 200
        expected = {'job_id': str(i),
                    'url': 'url',
                    'job_type': 'docket',
                    'reg_id': 3,
                    'agency': 'EPA'
                    }
        assert response.get_json() == expected


def test_success_logging_output_for_put_results(capsys, mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({
        'job_id': 2,
        'directory': 'dir/dir',
        'job_type': 'dockets',
        'results': {'data': {
            'type': 'dockets'
            }
        }
    })
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    assert len(mock_server.data.added) == 1
    captured = capsys.readouterr()
    print_msgs = [
        'Work_server received job for client:  1\n',
        'Wrote job dir, job_id: 2, to dir/dir\n',
        'SUCCESS: client:1, job: 2\n'
    ]
    assert captured.out == "".join(print_msgs)


def test_success_logging_for_no_attachment_results(capsys, mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({
        'job_id': 2,
        'job_type': 'attachments',
        'results': {},
        'reg_id': 3,
        'agency': 4
    })
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    assert len(mock_server.data.attachments_added) == 0
    captured = capsys.readouterr()
    print_data = []
    assert captured.out == "".join(print_data)
