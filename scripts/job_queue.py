# pylint: disable=too-many-arguments
import sys
import pika


class RabbitMQ:
    """
    Encapsulate calls to RabbitMQ in one place
    """

    def __init__(self, queue_name):
        """
        Create a new RabbitMQ object
        @param queue_name: the name of the queue to use
        """
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

    def _ensure_channel(self):
        if self.connection is None or not self.connection.is_open:
            connection_parameter = pika.ConnectionParameters("localhost")
            self.connection = pika.BlockingConnection(connection_parameter)
            self.channel = self.connection.channel()
            self.channel.queue_declare(self.queue_name, durable=True)

    def size(self) -> int:
        """
        Get the number of jobs in the queue.
        Can't be sure Channel is active between ensure_channel()
        and queue_declare() which is the reasoning for implementation of try
        except
        @return: a non-negative integer
        """
        self._ensure_channel()
        try:
            queue = self.channel.queue_declare(self.queue_name, durable=True)
            return queue.method.message_count
        except pika.exceptions.StreamLostError:
            print("FAILURE: RabbitMQ Channel Connection Lost", file=sys.stderr)
            return 0
