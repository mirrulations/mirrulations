class RedisConnector():
    def __init__(self, redis):
        self.redis = redis

    def pop_from_list(self, list_name):
        return self.redis.lpop(list_name)

    def push_to_list(self, list_name, value):
        self.redis.lpush(list_name, value)

    def add_to_hash(self, hash_name, key, value):
        return self.redis.hset(hash_name, key, value)

    def get_from_hash(self, hash_name, key):
        return self.redis.hget(hash_name, key)
