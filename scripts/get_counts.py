#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from counts import Counts, CountsEncoder
from job_queue import RabbitMQ

import redis
import requests

REGULATIONS_BASE_URL = "https://api.regulations.gov/v4/"


class MissingRedisKeyException(Exception):
    pass


def _download_regulation_count(
    url: str, headers: dict[str, str], params: dict[str, str]
) -> int:
    response = requests.get(
        url,
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()["meta"]["totalElements"]


def get_regulation(api_key: str, last_timestamp: dt.datetime) -> Counts:
    """Get counts from regulations.gov given a last_timestamp

    Exactly 6 Regulations.gov API calls are made during this function
    """
    output: Counts = {
        "creation_timestamp": dt.datetime.now(dt.timezone.utc),
        "queue_size": 0,
        "dockets": {
            "downloaded": -1,
            "jobs": 0,
            "total": -1,
            "last_timestamp": last_timestamp,
        },
        "documents": {
            "downloaded": -1,
            "jobs": 0,
            "total": -1,
            "last_timestamp": last_timestamp,
        },
        "comments": {
            "downloaded": -1,
            "jobs": 0,
            "total": -1,
            "last_timestamp": last_timestamp,
        },
    }

    headers = {"X-Api-Key": api_key}
    # NOTE: we set pagesize to be 5 since we only care about the metadata
    downloaded_filter = {
        "filter[lastModifiedDate][le]": last_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "page[size]": 5,
    }

    for entity_type in ("dockets", "documents", "comments"):
        downloaded = _download_regulation_count(
            REGULATIONS_BASE_URL + entity_type, headers, downloaded_filter
        )
        total = _download_regulation_count(
            REGULATIONS_BASE_URL + entity_type, headers, {"page[size]": "5"}
        )
        output[entity_type]["downloaded"] = downloaded
        output[entity_type]["total"] = total

    return output


def get_dashboard(dashboard_url: str, last_timestamp: dt.datetime) -> Counts:
    """Get the counts of a running mirrulations instance via it's dashboard"""
    response = requests.get(dashboard_url + "/data")
    response.raise_for_status()

    content = response.json()

    counts: Counts = {
        "creation_timestamp": dt.datetime.now(dt.timezone.utc),
        "queue_size": content["num_jobs_waiting"],
        "dockets": {
            "downloaded": content["num_dockets_done"],
            "jobs": content["num_jobs_dockets_queued"],
            "total": content["regulations_total_dockets"],
            "last_timestamp": last_timestamp,
        },
        "documents": {
            "downloaded": content["num_documents_done"],
            "jobs": content["num_jobs_documents_queued"],
            "total": content["regulations_total_documents"],
            "last_timestamp": last_timestamp,
        },
        "comments": {
            "downloaded": content["num_comments_done"],
            "jobs": content["num_jobs_comments_queued"],
            "total": content["regulations_total_comments"],
            "last_timestamp": last_timestamp,
        },
    }

    return counts


def _get_key_or_raise(db: redis.Redis, key: str) -> str:
    value: str | None = db.get(key)
    if value is None:
        raise MissingRedisKeyException(f"missing redis key: {key}")

    return value


def get_redis(db: redis.Redis) -> Counts:
    """Get the counts of a running mirrulations instance via a Redis connection"""

    counts: Counts = {
        "creation_timestamp": dt.datetime.now(dt.timezone.utc),
    }
    queue = RabbitMQ("jobs_waiting_queue")
    counts["queue_size"] = queue.size()

    for entity_type in ("dockets", "documents", "comments"):
        # Getting any of these values can raise an exception
        downloaded = _get_key_or_raise(db, f"num_{entity_type}_done")
        jobs = _get_key_or_raise(db, f"num_jobs_{entity_type}_waiting")
        total = _get_key_or_raise(db, f"regulations_total_{entity_type}")
        last_timestamp = _get_key_or_raise(db, f"{entity_type}_last_timestamp")

        counts[entity_type] = {
            "downloaded": int(downloaded),
            "jobs": int(jobs),
            "total": int(total),
            "last_timestamp": dt.datetime.strptime(last_timestamp, "%Y-%m-%d %H:%M:%S"),
        }

    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Get Counts",
        description="Get Docket, Document, and Comment counts from multiple sources",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        type=str,
        default="-",
        help="file to output to, use '-' for stdout (default '%(default)s')",
    )
    subparsers = parser.add_subparsers(
        dest="source", required=True, help="The source to get counts from"
    )

    regulations = subparsers.add_parser(
        "regulations", help="download counts from regulations.gov"
    )
    regulations.add_argument(
        "-a",
        "--api-key",
        help="Regulations.gov api key, defaults to value of `API_KEY` environment variable",
        default=os.getenv("API_KEY"),
        type=str,
    )
    regulations.add_argument(
        "-t",
        "--last-timestamp",
        metavar="TIMESTAMP",
        type=dt.datetime.fromisoformat,
        default=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        help="last timestamp that is assumed to have been downloaded in ISO 8601 format 'YYYY-MM-DDTHH:mm:ssZ' (default '%(default)s')",
    )

    dashboard = subparsers.add_parser(
        "dashboard", help="get counts from a mirrulations dashboard"
    )
    dashboard.add_argument(
        "-u",
        "--url",
        metavar="DASHBOARD_URL",
        default="http://localhost",
        help="dashboard url (default '%(default)s')",
    )
    dashboard.add_argument(
        "last_timestamp",
        type=dt.datetime.fromisoformat,
        default=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        help="last timestamp that is assumed to have been downloaded in ISO 8601 format 'YYYY-MM-DDTHH:mm:ss' (default '%(default)s')",
    )

    redis_args = subparsers.add_parser("redis", help="get counts from redis")
    redis_args.add_argument(
        "--hostname",
        metavar="HOSTNAME",
        default="localhost",
        help="redis server hostname (default '%(default)s')",
    )
    redis_args.add_argument(
        "-p",
        "--port",
        metavar="PORT",
        type=int,
        default=6379,
        help="port for redis server (default '%(default)s')",
    )
    redis_args.add_argument(
        "-n",
        "--db",
        metavar="DB_NUMBER",
        type=int,
        default=0,
        help="redis database number (default '%(default)s')",
    )

    args = parser.parse_args()

    source = args.source
    if source == "regulations":
        api_key = args.api_key
        if api_key is None or api_key == "":
            print("No api key found, exitting", file=sys.stderr)
            sys.exit(1)
        output = get_regulation(api_key, args.last_timestamp)
    elif source == "dashboard":
        output = get_dashboard(args.url, args.last_timestamp)
    elif source == "redis":
        db = redis.Redis(
            host=args.hostname, port=args.port, db=args.db, decode_responses=True
        )
        try:
            output = get_redis(db)
        except MissingRedisKeyException as e:
            print(f"Missing a redis key, exitting\n{e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Unrecognized source, exitting", file=sys.stderr)
        sys.exit(1)

    if args.output == "-":
        json.dump(output, sys.stdout, cls=CountsEncoder)
    else:
        with open(pathlib.Path(args.output), "w") as fp:
            json.dump(output, fp, cls=CountsEncoder)
