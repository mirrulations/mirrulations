from mirrcore.rabbitmq import RabbitMQ


class JobQueue:
    """
    This class is an abstraction of the process of adding and
    getting jobs.  It hides the implementation details of
    how jobs are stored in a DB/memory.
    """

    def __init__(self, database):
        self.database = database
        self.rabbitmq = RabbitMQ()

        if not self.database.exists('num_jobs_attachments_waiting'):
            self.database.set('num_jobs_attachments_waiting', 0)
        if not self.database.exists('num_jobs_comments_waiting'):
            self.database.set('num_jobs_comments_waiting', 0)
        if not self.database.exists('num_jobs_documents_waiting'):
            self.database.set('num_jobs_documents_waiting', 0)
        if not self.database.exists('num_jobs_dockets_waiting'):
            self.database.set('num_jobs_dockets_waiting', 0)

    def add_job(self, url, job_type=None, reg_id=None, agency=None):
        job_id = self.get_job_id()
        job = {
            'job_id': job_id,
            'url': url,
            'job_type': job_type,
            'reg_id': reg_id,
            'agency': agency
            }
        self.rabbitmq.add(job)
        if job_type == 'attachments':
            self.database.incr('num_jobs_attachments_waiting')
        elif job_type == 'comments':
            self.database.incr('num_jobs_comments_waiting')
        elif job_type == 'documents':
            self.database.incr('num_jobs_documents_waiting')
        elif job_type == 'dockets':
            self.database.incr('num_jobs_dockets_waiting')

    def get_num_jobs(self):
        return self.rabbitmq.size()

    def get_job_stats(self):
        jobs_waiting = self.get_num_jobs()
        jobs_in_progress = int(self.database.hlen('jobs_in_progress'))
        jobs_total_minus_jobs_done = jobs_waiting + jobs_in_progress

        client_ids = self.database.get('total_num_client_ids')
        clients_total = int(client_ids) if client_ids is not None else 0

        return {
            'num_jobs_waiting': jobs_waiting,
            'num_jobs_in_progress':
                int(self.database.hlen('jobs_in_progress')),
            'jobs_total': jobs_total_minus_jobs_done,
            'clients_total': clients_total,
            'num_jobs_attachments_queued':
                int(self.database.get('num_jobs_attachments_waiting')),
            'num_jobs_comments_queued':
                int(self.database.get('num_jobs_comments_waiting')),
            'num_jobs_documents_queued':
                int(self.database.get('num_jobs_documents_waiting')),
            'num_jobs_dockets_queued':
                int(self.database.get('num_jobs_dockets_waiting'))
        }

    def get_job(self):
        return self.rabbitmq.get()

    def get_job_id(self):
        job_id = self.database.incr('last_job_id')
        return job_id

    def get_last_timestamp_string(self, endpoint):
        key = f'{endpoint}_last_timestamp'
        if self.database.exists(key):
            return self.database.get(key).decode()
        return '1972-01-01 00:00:00'

    def set_last_timestamp_string(self, endpoint, date_string):
        key = f'{endpoint}_last_timestamp'
        self.database.set(key, date_string.replace('T', ' ')
                          .replace('Z', ''))

   