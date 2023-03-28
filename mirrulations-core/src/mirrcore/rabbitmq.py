import json
import pika
from mirrcore.job_queue_exceptions import JobQueueException


class RabbitMQ:
    """
    Encapsulate calls to RabbitMQ in one place
    """

    def __init__(self):
        self.connection = None
        self.channel = None

    def _ensure_channel(self):
        if self.connection is None or not self.connection.is_open:
            connection_parameter = pika.ConnectionParameters('rabbitmq')
            self.connection = pika.BlockingConnection(connection_parameter)
            self.channel = self.connection.channel()
            self.channel.queue_declare('jobs_waiting_queue', durable=True)

    def add(self, job):
        """
        Add a job to the channel
        @param job: the job to add
        @return: None
        """
        self._ensure_channel()
        # channel cannot be ensured hasn't dropped been between these calls
        try:
            persistent_delivery = pika.spec.PERSISTENT_DELIVERY_MODE
            self.channel.basic_publish(exchange='',
                                       routing_key='jobs_waiting_queue',
                                       body=json.dumps(job),
                                       properties=pika.BasicProperties(
                                        delivery_mode=persistent_delivery)
                                       )
        except pika.exceptions.StreamLostError as error:
            print("FAILURE: RabbitMQ Channel Connection Lost")
            raise JobQueueException from error

    def size(self):
        """
        Get the number of jobs in the queue.
        Can't be sure Channel is active between ensure_channel()
        and queue_declare() which is the reasoning for implementation of try
        except
        @return: a non-negative integer
        """
        self._ensure_channel()
        try:
            queue = self.channel.queue_declare('jobs_waiting_queue',
                                               durable=True)
            return queue.method.message_count
        except pika.exceptions.StreamLostError as error:
            print("FAILURE: RabbitMQ Channel Connection Lost")
            raise JobQueueException from error

    def get(self):
        """
        Take one job from the queue and return it
        @return: a job, or None if there are no jobs
        """
        # Check if channel is up, if not, create a new one
        self._ensure_channel()
        try:
            get_channel = self.channel.basic_get('jobs_waiting_queue')
            get_job_waiting_queue = get_channel
            frames = get_job_waiting_queue
            method_frame = frames[0]
            body = frames[2]
            # If there was no job available
            if method_frame is None:
                return None
            self.channel.basic_ack(method_frame.delivery_tag)
            return json.loads(body.decode('utf-8'))
        except pika.exceptions.StreamLostError as error:
            print("FAILURE: RabbitMQ Channel Connection Lost")
            raise JobQueueException from error
