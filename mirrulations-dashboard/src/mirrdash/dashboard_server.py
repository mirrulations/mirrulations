"""
This module creates the dashboard application that queries
    the redis and mongo databases to return stats about
    the number of jobs in progress/complete and the status
    of the containers.

Dependencies:
    docker, dotenv, flask, flask_cors, os, pymongo, redis
"""
import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from mirrcore.job_queue import JobQueue
from mirrcore.job_queue_exceptions import JobQueueException
from mirrdash.sum_mongo_counts import connect_mongo_db, get_done_counts
from dotenv import load_dotenv
from redis import Redis
import docker


class Dashboard:
    def __init__(self, job_queue, docker_server, mongo_client):
        self.app = Flask(__name__)
        self.job_queue = job_queue
        self.docker = docker_server
        self.mongo = mongo_client
        CORS(self.app, resources={r'/data': {'origins': '*'}})
        CORS(self.app, resources={r'/devdata': {'origins': '*'}})


def get_jobs_stats(job_queue):
    return job_queue.get_job_stats()


def get_container_stats(client):
    stats = {}
    for container in client.containers.list():
        name = get_container_name(container.name)
        status = container.status
        stats[name] = status
    return stats


def get_container_name(container_name):
    """
    Docker container names may be created with hyphens,
    so we replace them with underscores.
    """
    name = container_name.replace('-', '_')
    long_name_lst = name.split('_')
    long_name_lst.pop(0)
    long_name_lst.pop(-1)
    return '_'.join(long_name_lst)


def create_server(job_queue, docker_server, mongo_client):
    dashboard = Dashboard(job_queue, docker_server, mongo_client)

    @dashboard.app.route('/', methods=['GET'])
    def _index():
        return render_template(
            'index.html'
        )

    @dashboard.app.route('/dev', methods=['GET'])
    def _dev():
        return render_template(
            'dev.html'
        )

    @dashboard.app.route('/data', methods=['GET'])
    def _get_client_dashboard_data():
        """ returns data as json and request status code """
        try:
            data = get_jobs_stats(dashboard.job_queue)
        except JobQueueException as error:
            print(f"FAILURE: Encountered JobQueueException from {error}")
            # Index.js expects some values to update. by providing None or
            # 'null' to num_jobs_waiting (supposed to be an int), dashboard
            # javascript will recognize something went wrong and reflect status
            return {'num_jobs_waiting': None}, error.status_code

        # Get the number of jobs done from the mongo db
        # and add it to the data
        jobs_done_info = get_done_counts(dashboard.mongo, 'mirrulations')
        data.update(jobs_done_info)

        # Add this value to the total jobs
        data['jobs_total'] += jobs_done_info['num_jobs_done']

        return jsonify(data), 200

    @dashboard.app.route('/devdata', methods=['GET'])
    def _get_developer_dashboard_data():
        """ returns data as json and request status code """

        # Add container info to data
        data = get_container_stats(dashboard.docker)

        return jsonify(data), 200

    return dashboard


if __name__ == '__main__':
    load_dotenv()
    mongo_host = os.getenv('MONGO_HOSTNAME')
    the_job_queue = JobQueue(Redis(os.getenv('REDIS_HOSTNAME')))
    server = create_server(the_job_queue,
                           docker.from_env(),
                           connect_mongo_db(mongo_host, 27017))
    server.app.run(port=5000)
