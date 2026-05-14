import time
import redis


def is_redis_available(database):
    try:
        return database.ping()
    except (ConnectionRefusedError, redis.BusyLoadingError):
        return False


def load_redis(wait_time=1):
    '''
    Returns an instance of a Redis client.
    Blocks until Redis is confirmed to be running.
    wait_time: number of seconds to wait before checking if Redis is available.
    '''
    database = redis.Redis('redis')

    while is_redis_available(database) is False:
        print('Redis database is busy loading')
        time.sleep(wait_time)

    return database
