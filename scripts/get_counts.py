#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from typing import Any, TypedDict

import redis
import requests

REGULATIONS_BASE_URL = "https://api.regulations.gov/v4/"


class Counts(TypedDict):
    dockets: int
    documents: int
    comments: int


class EntityCount(TypedDict):
    downloaded: int
    total: int


class Output(TypedDict):
    start_timestamp: dt.datetime
    stop_timestamp: dt.datetime
    dockets: EntityCount
    documents: EntityCount
    comments: EntityCount


class OutputEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, dt.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(o)


def get_regulation_count(api_key: str, start: dt.datetime, end: dt.datetime) -> Counts:
    headers = {"X-Api-Key": api_key}
    counts: Counts = {"dockets": -1, "documents": -1, "comments": -1}

    params = {
        "filter[lastModifiedDate][ge]": start.strftime("%Y-%m-%d %H:%M:%S"),
        "filter[lastModifiedDate][le]": end.strftime("%Y-%m-%d %H:%M:%S"),
    }

    for type_ in counts:
        response = requests.get(
            REGULATIONS_BASE_URL + type_, headers=headers, params=params
        )
        response.raise_for_status()
        counts[type_] = response.json()["meta"]["totalElements"]

    return counts


def get_true_prod_count(dashboard_url: str) -> Counts:
    """Dumbly get the counts of a running mirrulations instance"""
    response = requests.get(dashboard_url + "/data")
    response.raise_for_status()

    stats = response.json()
    counts = Counts(
        dockets=stats["num_dockets_done"],
        documents=stats["num_documents_done"],
        comments=stats["num_comments_done"],
    )

    return counts


def clamp_counts(counts: Counts, max_counts: Counts) -> Counts:
    clamped = Counts(dockets=0, documents=0, comments=0)
    for key in counts:
        if max_counts[key] < counts[key]:
            clamped[key] = max(min(counts[key], max_counts[key]), 0)
        else:
            clamped[key] = counts[key]
    return clamped


def get_accurate_prod_count(
    db: redis.Redis, max_counts: Counts, ignore_queue: bool = False
) -> Counts:
    """Get the counts of a running mirrulations instance, ignoring duplicated downloads

    Args:
        db: a redis database connection
        strict: true if the resulting counts are allowed to be larger
                than the official Regulations.gov counts
        ignore_queue: continue even if jobs are in the queue
    """
    counts = Counts(
        dockets=int(db.get("num_dockets_done")),
        documents=int(db.get("num_documents_done")),
        comments=int(db.get("num_comments_done")),
    )
    jobs_waiting = {
        "dockets": int(db.get("num_jobs_dockets_waiting")),
        "documents": int(db.get("num_jobs_documents_waiting")),
        "comments": int(db.get("num_jobs_comments_waiting")),
    }

    if any(jobs_waiting.values()):
        if not ignore_queue:
            print("Jobs in queue, exitting", file=sys.stderr)
            sys.exit(1)
        for k in counts:
            counts[k] = min(max_counts[k] - jobs_waiting[k], counts[k])

    return clamp_counts(counts, max_counts)


def make_output(
    start: dt.datetime, end: dt.datetime, downloaded: Counts, total: Counts
) -> Output:
    output: Output = {
        "start_timestamp": start,
        "stop_timestamp": end,
        "dockets": {
            "downloaded": downloaded["dockets"],
            "total": total["dockets"],
        },
        "documents": {
            "downloaded": downloaded["documents"],
            "total": total["documents"],
        },
        "comments": {
            "downloaded": downloaded["comments"],
            "total": total["comments"],
        },
    }

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get Correct Mirrulation Counts as a json document",
        epilog="Can be used in conjunction with update_counts.py",
    )
    parser.add_argument(
        "-f",
        "--from",
        metavar="START_DATETIME",
        dest="start",
        type=dt.datetime.fromisoformat,
        default=dt.datetime(1776, 7, 4).isoformat(timespec="seconds"),
        help="start time (inclusive) for counts in ISO 8601 format 'YYYY-MM-DDTHH:mm:ss' (default '%(default)s')",
    )
    parser.add_argument(
        "-t",
        "--to",
        metavar="END_DATETIME",
        dest="end",
        type=dt.datetime.fromisoformat,
        default=dt.datetime.now().isoformat(timespec="seconds"),
        help="end time (exclusive) for counts in ISO 8601 format 'YYYY-MM-DDTHH:mm:ss' (default '%(default)s')",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="file to output to, use '-' for stdout (default '%(default)s')",
        type=str,
        default="-",
    )
    parser.add_argument(
        "-c",
        "--correct",
        help="Get corrected counts download counts",
        action="store_true",
    )
    parser.add_argument(
        "--ignore-queue", help="Continue if jobs are in the job queue", action="store_true"
    )
    parser.add_argument(
        "-a",
        "--api-key",
        help="Regulations.gov api key, defaults to value of `API_KEY` environment variable",
        default=os.getenv("API_KEY"),
        type=str,
    )
    parser.add_argument(
        "--dashboard",
        metavar="URL",
        help="URL of dashboard to use, mutually exclusive with '-c', (default '%(default)s')",
        default="http://localhost",
    )

    args = parser.parse_args()

    start: dt.datetime = args.start
    end: dt.datetime = args.end
    out_path: str = args.output
    correct: bool = args.correct
    dashboard_url: str = args.dashboard
    ignore_queue: bool = args.ignore_queue

    api_key = args.api_key
    if api_key is None or api_key == "":
        print("No api key found, exitting", file=sys.stderr)
        sys.exit(1)

    regulations = get_regulation_count(api_key, start, end)
    if correct:
        mirrulations = get_accurate_prod_count(redis.Redis(), regulations, ignore_queue)
    else:
        mirrulations = get_true_prod_count(dashboard_url)

    output = make_output(start, end, mirrulations, regulations)

    if out_path == "-":
        json.dump(output, sys.stdout, cls=OutputEncoder)
    else:
        with open(pathlib.Path(out_path), "w") as fp:
            json.dump(output, fp, cls=OutputEncoder)
