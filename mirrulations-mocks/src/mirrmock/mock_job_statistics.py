from mirrmock.mock_redis import MockRedisWithStorage


class MockJobStatistics:

    def __init__(self):
        self.cache = MockRedisWithStorage()
        self.extractions = []

    def increase_extractions_done(self):
        self.extractions.append(1)

    def get_jobs_done(self):
        return {
            'extractions': self.extractions
        }
