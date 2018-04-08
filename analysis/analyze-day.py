import argparse
import datetime
import json
import os
from glob import glob

import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--day", help="date YY-MM-DD", required=True)
    ap.add_argument("-i", "--ignore", type=int,
                    help="ignore events shorter then [s]")
    ap.add_argument("-s", "--sum", help="sum by keyword")
    ap.add_argument("-ndm", "--no_delete_morning", action='store_true',
                    help="do not filter out previous days night")
    ap.add_argument("-ind", "--ignore_next_day", action='store_true',
                    help="Ignore next day logs before wake up")
    args = ap.parse_args()
    day_filename = os.path.join(config.base_path, args.day)
    stream = load_stream(args, day_filename)
    if not args.ignore_next_day:
        next_day = datetime.datetime.strptime(args.day, "%y-%m-%d") + \
                   datetime.timedelta(days=1)
        day_filename = os.path.join(config.base_path,
                                    next_day.strftime("%y-%m-%d"))
        stream += load_stream(args, day_filename, only_morning=True)
    times = process_stream(stream)
    # todo add next day
    # todo estimate sleep time
    times.sort(key=lambda x: x["start"])
    print("-" * 10)
    print("STREAM")
    print("-" * 10)
    print_stream(args, times)
    print("-" * 10)
    print("SUMMARY")
    logged_time, unknown_time = logged_overall(args, times)
    print("Logged: {}".format(human_time_diff(logged_time)))
    print("Unknown: {}".format(human_time_diff(unknown_time)))
    print("-" * 10)
    summary, time_sum = get_summary(args, times)
    print_summary(logged_time, summary)
    print("-" * 10)
    if args.sum:
        print("{}: {}s".format(args.sum, human_time_diff(time_sum)))


def process_stream(stream):
    name = get_name(stream[0])
    item = stream[0]
    times = []
    last = None
    i = None
    # todo support multiple sources (overlap)
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
    return times


def load_stream(args, day_filename, only_morning=False):
    stream = []
    for i in glob(day_filename + "*.log"):
        if "err" not in i:
            machine = get_machine(i)
            for l in open(i):
                try:
                    s = json.loads(l)
                    s["source"] = machine
                    start_morning = is_morning(parse_time(s))
                    if (only_morning and start_morning) or (
                            not only_morning and (args.no_delete_morning
                                                  or not start_morning)):
                        stream.append(s)
                except Exception as e:
                    pass
                    # print("invalid json in {}, {}".format(i, e))
    stream.sort(key=lambda x: x["timestamp"])
    return stream


def print_summary(logged_time, summary):
    for k, v in summary:
        # todo top k
        # todo filter based on time / percent
        perc = (v / logged_time) * 100
        print("{}: {:.2f}% {}".format(human_time_diff(v), perc, k))


def get_summary(args, times):
    summary = {}
    time_sum = datetime.timedelta()
    for record in times:
        if args.sum and args.sum in get_name(record["item"]):
            time_sum += record["duration"]
        if is_none(record):
            continue
        name = get_name(record["item"])
        if name not in summary:
            summary[name] = datetime.timedelta()
        summary[name] += record["duration"]
    summary = sorted(summary.items(), key=lambda x: x[1], reverse=True)
    return summary, time_sum


def print_stream(args, times):
    for record in times:
        short = is_short(args, record)
        if not args.ignore or not short:
            print("{} {} {}: {}".format(
                record["start"].strftime("%H:%M:%S"),
                record["source"],
                human_time_diff(record["duration"]),
                get_name(record["item"])))


def logged_overall(args, times):
    logged_time = datetime.timedelta()
    unknown_time = datetime.timedelta()
    for record in times:
        if is_none(record):
            unknown_time += record["duration"]
        else:
            logged_time += record["duration"]
    return logged_time, unknown_time


def is_none(r):
    return r["source"] == "" and r["item"]["proc"] == "None" and \
           r["item"]["title"] == ""


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


def is_morning(t):
    return t.time() < config.morning


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
