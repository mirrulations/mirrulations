from flask import Flask, json, jsonify, request
import redis
from mirrcore.data_storage import DataStorage
from mirrcore.job_queue import JobQueue
from mirrcore.job_queue_exceptions import JobQueueException
from mirrserver.put_results_validator import PutResultsValidator
from mirrserver.exceptions import InvalidResultsException
from mirrserver.exceptions import InvalidClientIDException
from mirrserver.exceptions import MissingClientIDException
from mirrserver.exceptions import NoJobsException
from mirrserver.get_job_validator import GetJobValidator


class WorkServer:
    """
    Class between the client and the work generator.
    Handles the client's request to get a job, client id,
    and put job results.

    Attributes
    ----------
    app : Flask
        the flask app housing all 3 endpoints
    redis : redis
        the redis server holding the jobs waiting queue and client ids
    data : DataStorage
        the data storage class that connects to mongo
    put_results_validator : PutResultsValidator
        the validator class for the put results endpoint
    get_job_validator : GetJobValidator
        the validator class for the get job endpoint

    Methods
    -------
    __init__(self, redis_server)
        initializes the flask app, redis server
        data storage, attachment saver, and validators

    """
    def __init__(self, redis_server):
        """
        Parameters
        ----------
        redis_server : redis
            redis stores counts of types of jobs being processed

        job_queue: the queue from which jobs are accessed
        """
        self.app = Flask(__name__)
        self.redis = redis_server
        self.data = DataStorage()
        self.put_results_validator = PutResultsValidator()
        self.get_job_validator = GetJobValidator()
        self.job_queue = JobQueue(redis_server)


def check_for_database(workserver):
    """
    Checks if the database is connected
    if not this raises an exception

    Parameters
    ----------
    workserver : WorkServer
        the work server class

    Raises
    ------
    ConnectionError
        if the database is not connected
    """
    workserver.redis.ping()


def get_job(workserver):
    # pylint: disable=R0914
    """
    Takes client's put endpoints validates whether or not its a usable job
    if so it returns the job with the job ID, URL job_type and
    regulations id and agency so the job can be linked to related data
    in the databases

    Parameters
    ----------
    workserver : WorkServer
        the work server class

    Returns
    -------
    if valid job:
        True, job_id, url, job_type, reg_id, agency
    else:
        {'error': 'Client ID was not provided'}, 401
        {'error': 'No jobs available'}, 403
    """
    check_for_database(workserver)
    client_id = request.args.get('client_id')
    print("Attempting to get job")
    try:
        if workserver.job_queue.get_num_jobs() == 0:
            return False, jsonify({'error': 'No jobs available'}), 403
        job = workserver.job_queue.get_job()
        print("Job received from job queue")
    except JobQueueException:
        # if connection failed, no jobs to process
        return False, jsonify({'error': 'No jobs available'}), 503

    job_id = job['job_id']
    url = job['url']
    agency = job['agency'] if job.get('agency') else "other_agency"
    reg_id = job['reg_id'] if job.get('reg_id') else "other_reg_id"

    job_type = job.get('job_type', 'other')
    workserver.redis.hset('jobs_in_progress', job_id, url)
    workserver.redis.hset('client_jobs', job_id, client_id)

    workserver.job_queue.decrement_count(job_type)
    print(f'Job received: {job_type} for client: ', client_id)
    return True, job_id, url, job_type, reg_id, agency


def check_results(workserver, data, client_id):
    """
    checks that a result has a v
    id directory structure in the results key.
    Used for comments, documents, and dockets jobs
    so they know where to be saved to disk.

    Parameters
    ----------
    workserver : WorkServer
        the work server class
    data : dict
        the results data
    client_id : int
        the client id

    Returns
    -------

    if valid results:
        True, directory[:filename_start]
    else one of these options:
        {'error': 'The job being completed was not in progress'}
        {'error': 'No directory was included or was incorrect'}
        {'error': 'The client ID was incorrect'}
    """
    directory = data.get('directory')
    if directory is not None:
        filename_start = directory.rfind('/')
    if directory is None or filename_start == -1:
        error = {'error': 'No directory was included or was incorrect'}
        return False, jsonify(error), 403
    job_id = data.get('job_id', -1)
    expected_client_id = workserver.redis.hget('client_jobs', job_id)
    if (workserver.redis.hget('jobs_in_progress', job_id) is None or
            expected_client_id is None):
        error = {'error': 'The job being completed was not in progress'}
        return False, jsonify(error), 403
    if client_id != int(expected_client_id):
        error = {'error': 'The client ID was incorrect'}
        return False, jsonify(error), 403
    return (True, directory[:filename_start])


def check_received_result(workserver):
    check_for_database(workserver)
    client_id = request.args.get('client_id')
    print('Work_server received job for client: ', client_id)
    return True, client_id


def put_results(workserver, data):
    success, *values = check_received_result(workserver)
    if not success:
        return success, values[0], values[1]
    if 'error' in data['results'] or 'errors' in data['results']:
        job_id = data['job_id']
        result = workserver.redis.hget('jobs_in_progress', job_id)
        print(f"Errors in results. Adding job_url {result} to invalid_jobs")
        workserver.redis.hdel('jobs_in_progress', job_id)
        workserver.redis.hset('invalid_jobs', job_id, result)
        return (True,)
    success, *results = check_results(workserver, data, int(values[0]))
    if not success:
        return (success, *results)
    client_id = request.args.get('client_id')
    job_id = data['job_id']
    workserver.redis.hdel('jobs_in_progress', job_id)
    print(f"Wrote job {data['directory'].split('/')[-1]},"
          f" job_id: {job_id}, to {data['directory']}")
    workserver.data.add(data['results'])
    print(f'SUCCESS: client:{client_id}, job: {job_id}')
    return (True,)


def put_attachment_results(workserver, data):
    """
    Called to handle the functionality for an attachment job.
    Writes the results to disk and adds the results to the database.
    deletes the job from the redis job in progress queue

    Parameters
    ----------

    workserver : WorkServer
        the work server class
    data : dict
        the results data

    Returns
    -------
    if valid client id:
        True
    else:
        {'error': 'The client ID was incorrect'}, 401
    """
    success, *values = check_received_result(workserver)
    if not success:
        return success, values[0], values[1]
    # Not sure if we need the following two lines
    # since attachments aren't considered jobs?
    # job_id = data['job_id']
    # workserver.redis.hdel('jobs_in_progress', job_id)
    if data.get('results') is not None:
        print(f'Attachment from Comment {data["reg_id"]} \
        saved to {data["attachment_path"]}')
    workserver.data.add_attachment(data)
    return (True,)


def create_server(database):
    """
    Create Flask server, add endpoints, and return the server

    Parameters
    ----------
    database : redis
        the redis database

    Returns
    -------
    server : Flask
        the flask server
    """
    workserver = WorkServer(database)

    @workserver.app.route('/get_job', methods=['GET'])
    def _get_job():
        """
        The endpoint a client calls when requesting a job
        Handles the validation of json here and
        then does functionality in the get_job function

        Returns
        -------
        response : json
            {'job': {job_id: url, 'job_type': job_type}}
        """
        try:
            client_id = request.args.get('client_id')
            workserver.get_job_validator.check_get_jobs(client_id)
            success, *values = get_job(workserver)
            if not success:
                return tuple(values)
        except (MissingClientIDException, NoJobsException) as error:
            return jsonify(error.message), error.status_code
        except redis.exceptions.ConnectionError:
            return jsonify({'error': 'Cannot connect to the database'}), 500
        return jsonify({'job_id': str(values[0]),
                        'url':  values[1],
                        'job_type': values[2],
                        'reg_id': values[3],
                        'agency': values[4]}), 200

    @workserver.app.route('/put_results', methods=['PUT'])
    def _put_results():
        """
        The endpoint a client calls when returning with job results
        Handles the validation of json here and
        then does functionality in the put_results function

        Returns
        -------
        response : tuple(json, string)
            status code and message
        """
        data = json.loads(request.get_json())
        try:
            validator = workserver.put_results_validator.\
                check_put_results(data, request.args.get('client_id'))
        except (InvalidResultsException, InvalidClientIDException,
                MissingClientIDException) as invalid_result:
            return jsonify(invalid_result.message), invalid_result.status_code
        # Added ternary instead of if/else to please pylint too many statements
        if data['results'] == {}:
            return jsonify({'success': 'Job completed no attachments'}), 200
        success, *values = put_attachment_results(workserver, data) if \
            data.get('job_type') == 'attachments' else \
            put_results(workserver, data)
        if not success:
            return tuple(values)
        return jsonify(validator[0]), validator[1]

    return workserver


if __name__ == '__main__':
    try:
        r = redis.Redis('redis')
        r.keys('*')
        server = create_server(r)
        server.app.run(host='0.0.0.0', port=8080, debug=False)
    except redis.exceptions.ConnectionError:
        print('There is no Redis database to connect to.')
