import redis


def is_redis_available(database):
    try:
        return database.ping()
    except (ConnectionRefusedError, redis.BusyLoadingError):
        return False
