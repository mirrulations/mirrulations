import json
import logging
import time

import pika

from mirrcore.job_queue_exceptions import JobQueueException


def _snapshot_pika_log_levels():
    """Return ``{logger_name: level}`` for all ``pika`` names currently known."""
    levels = {}
    manager = logging.Logger.manager
    for name in list(manager.loggerDict.keys()):
        if isinstance(name, str) and name.startswith('pika'):
            lg = logging.getLogger(name)
            levels[name] = lg.level
    root = logging.getLogger('pika')
    levels.setdefault('pika', root.level)
    return levels


def _apply_pika_log_levels(levels_dict):
    for name, level in levels_dict.items():
        logging.getLogger(name).setLevel(level)


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
            connection_parameter = pika.ConnectionParameters('rabbitmq')
            self.connection = pika.BlockingConnection(connection_parameter)
            self.channel = self.connection.channel()
            self.channel.queue_declare(self.queue_name, durable=True)

    def wait_until_ready(self, poll_interval=1.0, timeout=None):
        """
        Block until the broker accepts an AMQP connection and the queue exists.

        Retries on connection failures (e.g. broker still starting). Failed
        attempts temporarily raise log levels on ``pika`` loggers so ERROR
        spam from the client library does not clutter operator logs.

        Parameters
        ----------
        poll_interval : float
            Seconds to sleep after a failed attempt before retrying.
        timeout : float or None
            If set, seconds before raising ``TimeoutError`` when unreachable.

        Raises
        ------
        TimeoutError
            If ``timeout`` elapses without a successful connection.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            snapshot = _snapshot_pika_log_levels()
            _apply_pika_log_levels(
                {name: logging.CRITICAL for name in snapshot})
            try:
                self._ensure_channel()
                return
            except (
                    pika.exceptions.AMQPConnectionError,
                    ConnectionError,
                    OSError,
            ):
                self.connection = None
                self.channel = None
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError(
                        f'RabbitMQ not reachable within {timeout} seconds'
                    ) from None
                time.sleep(poll_interval)
            finally:
                _apply_pika_log_levels(snapshot)

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
                                       routing_key=self.queue_name,
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
            queue = self.channel.queue_declare(self.queue_name,
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
            get_channel = self.channel.basic_get(self.queue_name)
            method_frame = get_channel[0]
            body = get_channel[2]
            # If there was no job available
            if method_frame is None:
                return None
            self.channel.basic_ack(method_frame.delivery_tag)
            return json.loads(body.decode('utf-8'))
        except pika.exceptions.StreamLostError as error:
            print("FAILURE: RabbitMQ Channel Connection Lost")
            raise JobQueueException from error
