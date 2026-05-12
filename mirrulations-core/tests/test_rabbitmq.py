# pylint: disable=unused-argument
from unittest.mock import MagicMock

import pika
import pytest

from mirrcore.job_queue_exceptions import JobQueueException
from mirrcore.rabbitmq import RabbitMQ


class ChannelSpy:
    """
    This test exists to increase coverage.  The RabbitMQ class encapsulates
    interactions with RabbitMQ.  We don't need to test the pika class,
    so this test simply calls all the methods using a mock. In this case,
    unused arguments are needed, so pylint will be disabled for this case.
    """

    def queue_declare(self, *args, **kwargs):
        return MagicMock()

    def basic_publish(self, *args, **kwargs):
        pass

    def basic_get(self, *args, **kwargs):
        return None, None, None


class PikaSpy:

    def __init__(self, *args, **kwargs):
        self.is_open = True

    def channel(self, *args, **kwargs):
        return ChannelSpy()


class BadPikaSpy:
    def __init__(self, *args, **kwargs):
        self.is_open = True

    def channel(self, *args, **kwargs):
        return BadConnectionSpy()


class BadConnectionSpy:
    def queue_declare(self, *args, **kwargs):
        return MagicMock()

    def basic_publish(self, *args, **kwargs):
        raise pika.exceptions.StreamLostError()

    def basic_get(self, *args, **kwargs):
        raise pika. exceptions.StreamLostError()


def test_rabbit_interactions(monkeypatch):

    monkeypatch.setattr(pika, 'BlockingConnection', PikaSpy)

    rabbit = RabbitMQ('jobs_waiting_queue')
    rabbit.add('foo')
    rabbit.size()
    rabbit.get()


def test_rabbit_error_interactions(monkeypatch):
    monkeypatch.setattr(pika, 'BlockingConnection', BadPikaSpy)

    rabbitmq = RabbitMQ('jobs_waiting_queue')

    # Ensure that the exception is raised when add() is called
    with pytest.raises(JobQueueException):
        rabbitmq.add('foo')

    # Ensure that the exception is caught and re-raised as a
    # JobQueueException in get()
    with pytest.raises(JobQueueException):
        rabbitmq.get()


def test_wait_until_ready_retries_then_succeeds(monkeypatch):
    attempts = {'n': 0}

    def flaky_blocking(*args, **kwargs):
        attempts['n'] += 1
        if attempts['n'] < 3:
            raise pika.exceptions.AMQPConnectionError('connection refused')
        return PikaSpy()

    monkeypatch.setattr(pika, 'BlockingConnection', flaky_blocking)
    rabbit = RabbitMQ('jobs_waiting_queue')
    rabbit.wait_until_ready(poll_interval=0)

    assert attempts['n'] == 3
    assert rabbit.connection is not None


def test_wait_until_ready_timeout(monkeypatch):
    def always_fail(*args, **kwargs):
        raise pika.exceptions.AMQPConnectionError('refused')

    monkeypatch.setattr(pika, 'BlockingConnection', always_fail)
    rabbit = RabbitMQ('jobs_waiting_queue')

    with pytest.raises(TimeoutError):
        rabbit.wait_until_ready(poll_interval=0.01, timeout=0.05)
