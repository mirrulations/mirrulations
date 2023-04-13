from mirrmock.mock_redis import MockRedisWithStorage


class MockJobStatistics:

    def __init__(self):
        self.cache = MockRedisWithStorage()
