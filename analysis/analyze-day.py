import argparse
import json
import os
import sys
from glob import glob

import config
import datetime


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--day", help="date YY-MM-DD")
    ap.add_argument("-i", "--ignore", type=int,
                    help="ignore events shorter then [s]")
    args = ap.parse_args()
    if args.day is None:
        print("Please provide the date for analysis\n\n")
        ap.print_help()
        sys.exit(1)
    day_filename = os.path.join(config.base_path, args.day)
    stream = []
    for i in glob(day_filename + "*.log"):
        if "err" not in i:
            machine = get_machine(i)
            for l in open(i):
                try:
                    s = json.loads(l)
                    s["source"] = machine
                    stream.append(s)
                except Exception as e:
                    pass
                    # print("invalid json in {}, {}".format(i, e))
    stream.sort(key=lambda x: x["timestamp"])
    start = parse_time(stream[0])
    name = get_name(stream[0])
    for i in stream[1:]:
        if get_name(i) != name:
            duration = parse_time(i) - start
            if not args.ignore or duration.total_seconds() > args.ignore:
                print("{} {}: {}".format(start.strftime("%H:%M:%S"),
                                            human_time_diff(duration),
                                            get_name(i)))
            start = parse_time(i)
            name = get_name(i)


def human_time_diff(diff):
    h = diff.seconds // 60 // 60
    m = diff.seconds // 60 - (h * 60)
    s = diff.seconds - (m * 60)
    if h > 0:
        return "{}h {}m {}s".format(h, m, s)
    if m > 0:
        return "{}m {}s".format(m, s)
    return "{:.2f}s".format(s + (diff.microseconds / 10 ** 6))


def parse_time(entry):
    return datetime.datetime.fromtimestamp(entry["timestamp"])


def get_name(entry):
    return "{}-{}".format(entry.get("proc", ""), entry.get("title", ""))


def get_machine(log_filepath):
    filename = os.path.basename(log_filepath)
    return filename.split('.')[-2]


if __name__ == '__main__':
    main()
