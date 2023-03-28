import redis


class BusyRedis():
    """
    Stub for testing in place of a Redis server that is busy loading the data
    to memory, ping replies with true
    """
    def ping(self):
        raise redis.BusyLoadingError


class ReadyRedis():
    """
    Stub for testing in place of an active Redis server,
    ping replies with true
    """
    def ping(self):
        return True


class MockRedisWithStorage():
    """
    Mock for testing in place of an active Redis server that has storage
    """
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        if key is None:
            self.data[key] = int(0)
        self.data[f'{key}'] = value

    def exists(self, key):
        return key in self.data

    def get(self, key):
        return self.data[f'{key}']

    def incr(self, key):
        try:
            self.data[key] += 1
        except KeyError:
            # self.data.set(key, 0)
            self.data[key] = 0
            self.data[key] += 1

    def decr(self, key):
        try:
            self.data[key] -= 1
        except KeyError:
            # self.data.set(key, 0)
            self.data[key] = 0
            self.data[key] -= 1

    def lpush(self, key, val):
        try:
            self.data[key] = [val]+self.data[key]
        except KeyError:
            self.data[key] = []
            self.data[key] = [val]+self.data[key]
