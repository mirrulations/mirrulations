"""Client-specific exceptions."""


class RedisPingFailedError(Exception):
    """Redis did not respond to ping before dequeue."""


class SaveError(Exception):
    """Persisting payload to disk and/or remote storage failed."""


class APITimeoutException(Exception):
    """The Regulations.gov API did not respond in time."""
