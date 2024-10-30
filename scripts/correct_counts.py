#!/usr/bin/env python3

from copy import deepcopy
import json
import pathlib
import sys
from json import JSONDecodeError
from counts import Counts, CountsEncoder, CountsDecoder

import argparse


class JobsInQueueException(Exception):
    pass


def strategy_cap(recieved: Counts, ignore_queue: bool) -> Counts:
    filtered = deepcopy(recieved)
    no_changes = True
    if filtered["queue_size"] != 0 and not ignore_queue:
        raise JobsInQueueException(f'Found jobs in job queue: {filtered["queue_size"]}')
    for entity_type in ("dockets", "documents", "comments"):
        total_ = filtered[entity_type]["total"]
        downloaded = filtered[entity_type]["downloaded"]
        no_changes &= total_ > downloaded
        filtered[entity_type]["downloaded"] = min(total_, downloaded)

    if no_changes:
        print("No downloaded count exceeds it's total", file=sys.stderr)

    return filtered


def strategy_diff(recieved: Counts, ignore_queue: bool) -> Counts:
    filtered = deepcopy(recieved)
    for entity_type in ("dockets", "documents", "comments"):
        total_ = filtered[entity_type]["total"]
        downloaded = filtered[entity_type]["downloaded"]
        jobs = filtered[entity_type]["jobs"]
        if jobs > 0 and not ignore_queue:
            raise JobsInQueueException(
                f'{entity_type} has {filtered[entity_type]["jobs"]} in queue'
            )
        filtered[entity_type]["downloaded"] = min(total_ - jobs, downloaded)

    return filtered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Correct Counts",
        description="Correct counts in json format by either capping downloaded with `total` or capping with `total - jobs`",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT_PATH",
        type=str,
        default="-",
        help="file to output to, use '-' for stdout (default '%(default)s')",
    )
    parser.add_argument(
        "-i",
        "--input",
        metavar="INPUT_PATH",
        type=str,
        default="-",
        help="file to read from, use '-' for stdin (default '%(default)s')",
    )
    parser.add_argument(
        "-s",
        "--strategy",
        type=str,
        default="cap_with_total",
        choices=("cap_with_total", "diff_total_with_jobs"),
        help="the correction strategy to use (default '%(default)s')",
    )
    parser.add_argument(
        "--ignore-queue",
        action="store_true",
        help="continue even if there are queued jobs",
    )

    args = parser.parse_args()

    try:
        if args.input == "-":
            input_counts: Counts = json.load(sys.stdin, cls=CountsDecoder)
        else:
            try:
                with open(pathlib.Path(args.input), "r") as fp:
                    input_counts = json.load(fp, cls=CountsDecoder)
            except FileNotFoundError:
                print(f"Missing file {args.input}, exiting", file=sys.stderr)
                sys.exit(2)
    except JSONDecodeError:
        print(f"Malformed input file {args.input}, exiting", file=sys.stderr)
        sys.exit(2)

    try:
        if args.strategy == "cap_with_total":
            modified_counts = strategy_cap(input_counts, args.ignore_queue)
        elif args.strategy == "diff_total_with_jobs":
            modified_counts = strategy_diff(input_counts, args.ignore_queue)
        else:
            print(f"Unrecognized strategy {args.strategy}, exiting", file=sys.stderr)
            sys.exit(1)
    except JobsInQueueException as e:
        print(
            f"Found jobs in queue: {e}\nUse `--ignore-queue` to continue",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.output == "-":
        json.dump(modified_counts, sys.stdout, cls=CountsEncoder)
    else:
        with open(pathlib.Path(args.output), "w") as fp:
            json.dump(modified_counts, fp, cls=CountsEncoder)
