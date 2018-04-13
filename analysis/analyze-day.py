import argparse
import datetime
import json
import os
from glob import glob

import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--day", help="date YY-MM-DD")
    ap.add_argument("-db", "--day_back", type=int, default=0,
                    help="how many days before today")
    ap.add_argument("-i", "--ignore", type=int,
                    help="ignore events shorter then [s]")
    ap.add_argument("-sk", "--sum", help="sum by keyword")
    ap.add_argument("-ndm", "--no_delete_morning", action='store_true',
                    help="do not filter out previous days night")
    ap.add_argument("-ind", "--ignore_next_day", action='store_true',
                    help="Ignore next day logs before wake up")
    ap.add_argument("-s", "--stream", action='store_true',
                    help="Ignore stream")
    ap.add_argument("-k", "--summary_k", type=int,
                    help="Only k in summary")
    ap.add_argument("-p", "--summary_pct", type=int, default=1,
                    help="Only > pct in summary")
    ap.add_argument("-t", "--summary_time", type=int,
                    help="Only > time [s] in summary")
    args = ap.parse_args()
    date = args.day
    if not args.day:
        now = datetime.datetime.now()
        # working over midnight - want to see "today"
        if now.time() < config.morning:
            now -= datetime.timedelta(days=1)
        date = datetime.datetime.strftime(
            now - datetime.timedelta(days=args.day_back),
            "%y-%m-%d")
    print("Day {}".format(date))
    day_filename = os.path.join(config.base_path, date)
    stream = load_stream(args, day_filename)
    if not args.ignore_next_day:
        next_day = datetime.datetime.strptime(date, "%y-%m-%d") + \
                   datetime.timedelta(days=1)
        day_filename = os.path.join(config.base_path,
                                    next_day.strftime("%y-%m-%d"))
        stream += load_stream(args, day_filename, only_morning=True)
    if not stream:
        print("No data found")
        return
    times = process_stream(stream)
    # todo estimate sleep time
    times.sort(key=lambda x: x["start"])
    if args.stream:
        print("-" * 10)
        print("STREAM")
        print("-" * 10)
        print_stream(args, times)
    print("-" * 10)
    print("SUMMARY")
    logged_time, unknown_time = logged_overall(times)
    print("Logged: {}".format(human_time_diff(logged_time)))
    print("Unknown: {}".format(human_time_diff(unknown_time)))
    print("-" * 10)
    summary, time_sum = get_summary(args, times)
    print_summary(args, logged_time, summary)
    print("-" * 10)
    if args.sum:
        print("{}: {}s".format(args.sum, human_time_diff(time_sum)))


def process_stream(stream):
    name = get_name(stream[0])
    item = stream[0]
    times = []
    last = None
    i = None
    cnt = 0
    idle_sum = 0
    # todo support multiple sources (overlap)
    for i in stream[1:]:
        new_name = get_name(i)
        time_skip_val = i["timestamp"] - last["timestamp"] if last else 0
        time_skip = time_skip_val > 5
        found = False
        cnt += 1
        idle_sum += int(i.get("idletime", 0))
        if time_skip:
            # add time skip
            times.append(create_record(i, last, data={
                "timestamp": last["timestamp"],
                "proc": "None",
                "title": "",
            }))
            times.append(create_record(last, item, cnt=cnt, idle=idle_sum))
            found = True
        elif new_name != name:
            times.append(create_record(i, item, cnt=cnt, idle=idle_sum))
            found = True
        if found:
            name = get_name(i)
            item = i
            cnt = 0
            idle_sum = 0
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


def print_summary(args, logged_time, summary):
    summary = summary[:args.summary_k] if args.summary_k else summary
    print("time\tpercent\tchunks\tavg chunk\tavg idle\tname")
    for k, v in summary:
        duration = v.get("duration", datetime.timedelta())
        perc = (duration / logged_time) * 100
        if args.summary_pct and perc <= args.summary_pct:
            continue
        if args.summary_time and duration.total_seconds() < args.summary_time:
            continue
        # fmt_str = "{}: {:.2f}% chunks: {} | avg chunk: {} |" \
        #           " avg idle: {} | name: {}"
        fmt_str = "{}\t{:.2f}%\t{}\t{: <9}\t{: <8}\t{}"
        print(fmt_str.format(
            human_time_diff(duration),
            perc,
            v.get("groups_cnt", 1),
            human_time_diff(duration / v.get("groups_cnt", 1)),
            human_time_diff(
                datetime.timedelta(milliseconds=
                                   v.get("idle_sum", 0) / v.get("cnt", 1))),
            k
        ))


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
            summary[name] = {
                "duration": datetime.timedelta(),
                "cnt": 0,
                "groups_cnt": 0,
                "idle_sum": 0,
            }
        summary[name]["duration"] += record["duration"]
        summary[name]["cnt"] += record.get("cnt", 1)
        summary[name]["groups_cnt"] += 1
        summary[name]["idle_sum"] += record.get("idle_sum", 0)
    summary = sorted(summary.items(),
                     key=lambda x: x[1].get("duration",
                                            datetime.timedelta()),
                     reverse=True)
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


def logged_overall(times):
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


def create_record(end, start, data=None, cnt=1, idle=0):
    if not data:
        data = start
    return {
        "start": parse_time(start),
        "end": parse_time(end),
        "duration": parse_time(end) - parse_time(start),
        "source": data.get("source", ""),
        "item": data,
        "cnt": cnt,
        "idle_sum": idle,
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
