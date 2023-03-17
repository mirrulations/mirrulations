import pika
import json
import time

class RabbitMQ:
    """
    Encapsulate calls to RabbitMQ in one place
    """

    def __init__(self):
        self.connection = None
        self.channel = None

    def _ensure_channel(self):
        if self.connection is None or not self.connection.is_open:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            self.channel = self.connection.channel()
            self.channel.queue_declare('jobs_waiting_queue', durable=True)

    def add(self, job):
        """
        Add a job to the channel
        @param job: the job to add
        @return: None
        """
        self._ensure_channel()
        try:
            self.channel.basic_publish(exchange='',
                                       routing_key='jobs_waiting_queue',
                                       body=json.dumps(job),
                                       properties=pika.BasicProperties(
                                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                                       )
        except pika.exceptions.StreamLostError:
            print('FAILURE: Error occurred when adding a job. Sleeping...')
            time.sleep(60 * 60 * 4)

    def size(self):
        """
        Get the number of jobs in the queue
        @return: a non-negative integer
        """
        self._ensure_channel()
        queue = self.channel.queue_declare('jobs_waiting_queue', durable=True)
        return queue.method.message_count

    def get(self):
        """
        Take one job from the queue and return it
        @return: a job, or None if there are no jobs
        """
        # Connections timeout, so we have to create a new one each time
        self._ensure_channel()
        method_frame, header_frame, body = self.channel.basic_get('jobs_waiting_queue')
        # If there was no job available
        if method_frame is None:
            return None

        self.channel.basic_ack(method_frame.delivery_tag)
        return json.loads(body.decode('utf-8'))
