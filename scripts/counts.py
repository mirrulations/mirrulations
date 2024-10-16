import json
import datetime as dt
from typing import Any, TypedDict


class EntityCount(TypedDict):
    downloaded: int
    jobs: int
    total: int
    last_timestamp: dt.datetime


class Output(TypedDict):
    creation_timestamp: dt.datetime
    dockets: EntityCount
    documents: EntityCount
    comments: EntityCount


class OutputEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, dt.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(o)
