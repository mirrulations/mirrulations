import pika
import json

QUEUE = 'text_extract_waiting_queue'


class TextExtractQueue:
    """
    Class that encapsulates the rabbitmq queue for text extraction
    """

    def __init__(self):
        self.connection = None
        self.channel = None

    def _ensure_channel(self):
        if self.connection is None or not self.connection.is_open:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            self.channel = self.connection.channel()
            self.channel.queue_declare(QUEUE, durable=True)

    def add_extract_job(self, job):
        """
        Add a text extraction job to the channel
        @param job: the job to add
        """
        self._ensure_channel()
        try:
            self.channel.basic_publish(exchange='',
                                       routing_key=QUEUE,
                                       body=json.dumps(job),
                                       properties=pika.BasicProperties(
                                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                                       )
        except pika.exceptions.StreamLostError:
            print('FAILURE: Error occurred when adding a job. Sleeping...')

    def size(self):
        """
        Get the number of jobs in the queue
        @return: a non-negative integer
        """
        self._ensure_channel()
        queue = self.channel.queue_declare(QUEUE, durable=True)
        return queue.method.message_count

    def get_extract_job(self):
        """
        Take one job from the queue and return it
        @return: a job, or None if there are no jobs
        """
        # Connections timeout, so we have to create a new one each time
        self._ensure_channel()
        method_frame, header_frame, body = self.channel.basic_get(QUEUE)
        # If there was no job available
        if method_frame is None:
            return None

        self.channel.basic_ack(method_frame.delivery_tag)
        return json.loads(body.decode('utf-8'))
