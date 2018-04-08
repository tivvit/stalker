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
    ap.add_argument("-s", "--sum", help="sum by keyword")
    ap.add_argument("-ndm", "--no_delete_morning", action='store_true',
                    help="do not filter out previous days night")
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
    name = get_name(stream[0])
    item = stream[0]
    times = []
    last = None
    i = None
    # todo support multiple sources
    for i in stream[1:]:
        new_name = get_name(i)
        time_skip_val = i["timestamp"] - last["timestamp"] if last else 0
        time_skip = time_skip_val > 5
        if time_skip:
            # print("loggingg skip", time_skip_val)
            times.append({
                "start": parse_time(last),
                "end": parse_time(i),
                "duration": parse_time(i) - parse_time(last),
                "source": "",
                "item": {
                    "timestamp": last["timestamp"],
                    "proc": "None",
                    "title": "",
                }
            })
            times.append(create_record(last, item))
            name = get_name(i)
            item = i
        elif new_name != name:
            times.append(create_record(i, item))
            name = get_name(i)
            item = i
        last = i
    times.append(create_record(i, item))
    times.sort(key=lambda x: x["start"])
    time_sum = datetime.timedelta()
    for record in times:
        if args.sum and args.sum in get_name(record["item"]):
            time_sum += record["duration"]
        start_morning = is_morning(record)
        short = is_short(args, record)
        if (not args.ignore or not short) and (
                args.no_delete_morning or not start_morning):
            print("{} {} {}: {}".format(
                record["start"].strftime("%H:%M:%S"),
                record["source"],
                human_time_diff(record["duration"]),
                get_name(record["item"])))
    # todo add next day
    # todo estimate sleep time
    if args.sum:
        print("{}: {}s".format(args.sum, human_time_diff(time_sum)))


def create_record(i, item):
    return {
        "start": parse_time(item),
        "end": parse_time(i),
        "duration": parse_time(i) - parse_time(item),
        "source": item.get("source", ""),
        "item": item
    }


def is_short(args, record):
    return args.ignore and record["duration"].total_seconds() < args.ignore


def is_morning(record):
    return record["start"].time() < config.morning


def human_time_diff(diff):
    h = diff.seconds // 60 // 60
    m = diff.seconds // 60 - (h * 60)
    s = diff.seconds - ((h * 60 * 60) + (m * 60))
    if h > 0:
        return "{}h {}m {}s".format(h, m, s)
    if m > 0:
        return "{}m {}s".format(m, s)
    return "{:.2f}s".format(s + (diff.microseconds / 10 ** 6))


def parse_time(entry):
    return datetime.datetime.fromtimestamp(entry["timestamp"])


def get_name(entry):
    proc = match_proc(entry.get("proc", ""))
    return "{} {}".format(proc, entry.get("title", ""))


def match_proc(name):
    for i in config.mapping:
        if i in name:
            return config.mapping[i]
    return name


def get_machine(log_filepath):
    filename = os.path.basename(log_filepath)
    return filename.split('.')[-2]


if __name__ == '__main__':
    main()
