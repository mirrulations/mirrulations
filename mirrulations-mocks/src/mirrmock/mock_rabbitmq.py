class MockRabbit:

    def __init__(self):
        self.jobs = []

    def wait_until_ready(self, poll_interval=1.0, timeout=None):
        """No-op stand-in for :meth:`mirrcore.rabbitmq.RabbitMQ.wait_until_ready`."""

    def add(self, job):
        self.jobs.append(job)

    def size(self):
        return len(self.jobs)

    def get(self):
        return self.jobs.pop(0)
