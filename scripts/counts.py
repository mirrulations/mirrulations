import json
import datetime as dt
from typing import Any, TypedDict


class EntityCount(TypedDict):
    downloaded: int
    jobs: int
    total: int
    last_timestamp: dt.datetime


class Counts(TypedDict):
    creation_timestamp: dt.datetime
    queue_size: int
    dockets: EntityCount
    documents: EntityCount
    comments: EntityCount


class CountsEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, dt.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(o)


class CountsDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj: Any) -> Any:
        for key, value in obj.items():
            try:
                obj[key] = dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass
        return obj
