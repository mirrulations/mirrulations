from unittest.mock import MagicMock
from mirrcore.job_queue_exceptions import JobQueueException
from mirrcore.rabbitmq import RabbitMQ
import pika
import pytest

"""
This test exists to increase coverage.  The RabbitMQ class encapsulates
interactions with RabbitMQ.  We don't need to test the pika class,
so this test simply calls all the methods using a mock
"""


class ChannelSpy:

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

    r = RabbitMQ()
    r.add('foo')
    r.size()
    r.get()


def test_rabbit_error_interactions(monkeypatch):
    monkeypatch.setattr(pika, 'BlockingConnection', BadPikaSpy)

    rabbitmq = RabbitMQ()

    # Ensure that the exception is raised when add() is called
    with pytest.raises(JobQueueException):
        rabbitmq.add('foo')

    # Ensure that the exception is caught and re-raised as a JobQueueException in get()
    with pytest.raises(JobQueueException):
        rabbitmq.get()
