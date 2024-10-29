#!/usr/bin/env python3

import argparse
import json
import pathlib
import redis
import sys

from counts import Counts, CountsDecoder

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_BLINK = "\033[5m"
ANSI_BLINK_OFF = "\033[25m"
ANSI_FG_RED = "\033[31m"


def _get_vals(db: redis.Redis, entity_type: str) -> dict:
    done_raw: str | None = db.get(f"num_{entity_type}_done")
    if done_raw is not None:
        done = int(done_raw)
    else:
        done = "None"

    total_raw: str | None = db.get(f"regulations_total_{entity_type}")
    if total_raw is not None:
        total = int(total_raw)
    else:
        total = "None"

    timestamp: str = db.get(f"{entity_type}_last_timestamp") or "None"

    return {"done": done, "timestamp": timestamp, "total": total}


def _print_changes(info: str, original: str, new: str) -> None:
    if original != new:
        print(
            info,
            ANSI_FG_RED + ANSI_BOLD + original,
            f"{ANSI_BLINK}--->{ANSI_BLINK_OFF}",
            new + ANSI_RESET,
        )
    else:
        print(info, original, "--->", new)


def show_changes(db: redis.Redis, counts: Counts) -> None:
    for entity_type in ("dockets", "documents", "comments"):
        vals = _get_vals(db, entity_type)
        _print_changes(
            f"num_{entity_type}_done:\n  ",
            str(vals["done"]),
            str(counts[entity_type]["downloaded"]),
        )
        _print_changes(
            f"regulations_total_{entity_type}:\n  ",
            str(vals["total"]),
            str(counts[entity_type]["total"]),
        )
        _print_changes(
            f"{entity_type}_last_timestamp:\n  ",
            str(vals["timestamp"]),
            counts[entity_type]["last_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        )
        print()


def set_values(db: redis.Redis, counts: Counts):
    for entity_type in ("dockets", "documents", "comments"):
        try:
            db.set(f"num_{entity_type}_done", counts[entity_type]["downloaded"])
            db.set(f"regulations_total_{entity_type}", counts[entity_type]["total"])
            db.set(
                f"{entity_type}_last_timestamp",
                counts[entity_type]["last_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            )
        except Exception as e:
            print(
                f"Error occurred while setting values for {entity_type}, exitting",
                file=sys.stderr,
            )
            print(e)
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Set Counts", description="Set counts in Redis database from json"
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
        "-y",
        "--yes",
        dest="changes_confirmed",
        action="store_true",
        help="Do not check for confirmation when setting values",
    )
    parser.add_argument(
        "--host",
        metavar="HOSTNAME",
        default="localhost",
        help="redis server hostname (default '%(default)s')",
    )
    parser.add_argument(
        "-p",
        "--port",
        metavar="PORT",
        type=int,
        default=6379,
        help="port for redis server (default '%(default)s')",
    )
    parser.add_argument(
        "-n",
        "--db",
        metavar="DB_NUMBER",
        type=int,
        default=0,
        help="redis database number (default '%(default)s')",
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
                print(
                    f"Input file {args.input} does not exist, exitting", file=sys.stderr
                )
                sys.exit(2)
    except json.JSONDecodeError:
        print(f"Malformed input file {args.input}, exitting", file=sys.stderr)
        sys.exit(2)

    db = redis.Redis(args.host, args.port, args.db, decode_responses=True)
    changes_confirmed: bool = args.changes_confirmed

    if changes_confirmed:
        set_values(db, input_counts)
    else:
        show_changes(db, input_counts)
        response = (
            input("Are you sure you want to make the above changes [y/n]: ")
            .strip()
            .lower()
        )
        changes_confirmed = response == "y" or response == "yes"
        if changes_confirmed:
            set_values(db, input_counts)
        else:
            print("No values set, exitting")
            sys.exit()
