import argparse
import datetime
import json
import os
from glob import glob
import re

try:
    from . import config
except:
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
    ap.add_argument("-p", "--summary_pct", type=float, default=1,
                    help="Only > pct in summary")
    ap.add_argument("-t", "--summary_time", type=int,
                    help="Only > time [s] in summary")
    ap.add_argument("-idl", "--idle", type=int, default=60 * 10 ** 3,
                    help="> x ms is considered idle")
    ap.add_argument("-ss", "--save_stream", help="filename stream json")
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
    stream = load_stream(day_filename, no_delete_morning=args.no_delete_morning)
    if not args.ignore_next_day:
        next_day = datetime.datetime.strptime(date, "%y-%m-%d") + \
                   datetime.timedelta(days=1)
        day_filename = os.path.join(config.base_path,
                                    next_day.strftime("%y-%m-%d"))
        stream += load_stream(day_filename, only_morning=True)
    if not stream:
        print("No data found")
        return
    patterns = get_patterns()
    times = process_stream(stream, patterns, idle_time=args.idle)
    times = enrich_stream(times, patterns)
    # todo estimate sleep time
    times.sort(key=lambda x: x["start"])
    if args.stream:
        print("-" * 10)
        print("STREAM")
        print("-" * 10)
        print_stream(args, times, patterns)
    if args.save_stream:
        json.dump(times, open(args.save_stream, "w"),
                  default=json_serialization)
    print("-" * 10)
    print("SUMMARY")
    logged_time, unknown_time, idle_time = logged_overall(times)
    print("Logged: {}".format(human_time_diff(logged_time)))
    print("Idle: {}".format(human_time_diff(idle_time)))
    print("Unknown: {}".format(human_time_diff(unknown_time)))
    print("-" * 10)
    summary, time_sum = get_summary(args, times, patterns)
    print_summary(args, logged_time, summary)
    print("-" * 10)
    tag_analysis, tagged = analyze_tags(times)
    print_tag_summary(tag_analysis, tagged, logged_time)
    print("-" * 10)
    if args.sum:
        print("{}: {}s".format(args.sum, human_time_diff(time_sum)))


def json_serialization(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    if isinstance(o, datetime.timedelta):
        return o.total_seconds()


def process_stream(stream, patterns, idle_time=60 * 10 ** 3):
    times = []
    info = {}
    sources = set()

    for i in stream:
        source = i.get("source", "Unknown")
        idletime = int(i.get("idletime", 0)) if i.get("idletime", 0) else 0
        new_name = get_name(i, patterns)
        if source not in info:
            sources.add(source)
            info[source] = {
                "name": new_name,
                "item": i,
                "last": None,
                "cnt": 0,
                "idle_sum": 0,
                "last_idletime": idletime,
                "active": True if idletime < idle_time else False,
                "last_active": i,
            }
            continue
        # current info
        ci = info[source]
        time_skip_val = i["timestamp"] - ci["last"]["timestamp"] if \
            ci["last"] else 0
        time_skip = time_skip_val > 5
        refresh = False
        ci["cnt"] += 1
        ci["idle_sum"] += idletime
        if time_skip:
            # time_skip = missing entry = close and start again
            # todo check sums
            # Add time skip record
            times.append(create_record(ci["last"], i, data={
                "timestamp": ci["last"]["timestamp"],
                "proc": "None",
                "title": "",
            }))
            if ci["active"]:
                # close last active record
                times.append(
                    create_record(ci["item"], ci["last"], cnt=ci["cnt"],
                                  idle_sum=ci["idle_sum"]))
            else:
                # close last idle record
                times.append(
                    create_record(ci["last_active"], ci["last"], cnt=ci["cnt"],
                                  idle_sum=ci["idle_sum"],
                                  idle=True))
                ci["active"] = True
            refresh = True
            ci["last_active"] = i
        elif ci["active"]:
            if new_name != ci["name"]:
                times.append(create_record(ci["item"], i, cnt=ci["cnt"],
                                           idle_sum=ci["idle_sum"]))
                refresh = True
                ci["last_active"] = i
            if idletime > idle_time:
                # Add activity before idle
                times.append(create_record(ci["item"],
                                           ci["last_active"],
                                           cnt=ci["cnt"],
                                           idle_sum=ci["idle_sum"]))
                # todo idle_sum should be forwarded
                ci["active"] = False
                refresh = True
        elif not ci["active"] and idletime < ci["last_idletime"]:
            # idle end
            times.append(create_record(ci["last_active"], i, cnt=ci["cnt"],
                                       idle_sum=ci["idle_sum"],
                                       idle=True))
            refresh = True
            ci["active"] = True
        if refresh:
            ci["name"] = get_name(i, patterns)
            ci["item"] = i
            ci["cnt"] = 0
            ci["idle_sum"] = 0
        if idletime < ci["last_idletime"]:
            ci["last_active"] = i
        ci["last_idletime"] = idletime
        ci["last"] = i
    # add last one
    for s in sources:
        times.append(create_record(info[s]["item"], info[s]["last"]))
    return times


def enrich_stream(stream, patterns):
    for s in stream:
        s["tags"] = set()
        for p in patterns["title-tags"]:
            if p["re"].search(s["item"]["title"]):
                s["tags"].update(p["name"].split(','))
        for p in patterns["proc-tags"]:
            if p["re"].search(s["item"]["proc"]):
                s["tags"].update(p["name"].split(','))
    return stream


def load_stream(day_filename, no_delete_morning=False, only_morning=False):
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
                            not only_morning and (no_delete_morning
                                                  or not start_morning)):
                        stream.append(s)
                except Exception as e:
                    pass
                    # print("invalid json in {}, {}".format(i, e))
    stream.sort(key=lambda x: x["timestamp"])
    return stream


def print_summary(args, logged_time, summary):
    summary = summary[:args.summary_k] if args.summary_k else summary
    print("{: <12}\tpercent\tchunks\tavg chunk\tavg idle\tname".format("time"))
    for k, v in summary:
        duration = v.get("duration", datetime.timedelta())
        perc = (duration / logged_time) * 100
        if args.summary_pct and perc <= args.summary_pct:
            continue
        if args.summary_time and duration.total_seconds() < args.summary_time:
            continue
        # fmt_str = "{}: {:.2f}% chunks: {} | avg chunk: {} |" \
        #           " avg idle: {} | name: {}"
        fmt_str = "{: <12}\t{:.2f}%\t{}\t{: <9}\t{: <8}\t{}"
        print(fmt_str.format(
            human_time_diff(duration),
            perc,
            v.get("groups_cnt", 1),
            human_time_diff(duration / v.get("groups_cnt", 1)),
            human_time_diff(
                datetime.timedelta(milliseconds=
                                   v.get("idle_sum", 0) / v.get("cnt", 1))),
            "{} [{}]".format(k, ",".join(v["sources"]))
        ))


def get_summary(args, times, patterns):
    summary = {}
    time_sum = datetime.timedelta()
    for record in times:
        if args.sum and args.sum in get_name(record["item"], patterns):
            time_sum += record["duration"]
        if is_none(record):
            continue
        name = get_name(record["item"], patterns,
                        idle=record.get("idle", False))
        if name not in summary:
            summary[name] = {
                "duration": datetime.timedelta(),
                "cnt": 0,
                "groups_cnt": 0,
                "idle_sum": 0,
                "sources": set(),
            }
        summary[name]["duration"] += record["duration"]
        summary[name]["cnt"] += record.get("cnt", 1)
        summary[name]["groups_cnt"] += 1
        summary[name]["idle_sum"] += record.get("idle_sum", 0)
        summary[name]["sources"].add(record.get("source", "Unknown"))
    summary = sorted(summary.items(),
                     key=lambda x: x[1].get("duration",
                                            datetime.timedelta()),
                     reverse=True)
    return summary, time_sum


def print_stream(args, times, patterns):
    for record in times:
        short = is_short(args, record)
        if not args.ignore or not short:
            print("{} {} {}: {}".format(
                record["start"].strftime("%H:%M:%S"),
                record["source"],
                human_time_diff(record["duration"]),
                get_name(record["item"], patterns,
                         idle=record.get("idle", False))))


def logged_overall(times):
    # todo per device?
    # todo only active device
    logged_time = datetime.timedelta()
    unknown_time = datetime.timedelta()
    idle_time = datetime.timedelta()
    for record in times:
        if is_none(record):
            unknown_time += record["duration"]
        elif record.get("idle", False):
            idle_time += record["duration"]
        else:
            logged_time += record["duration"]
    return logged_time + idle_time, unknown_time, idle_time


def is_none(r):
    return r["source"] == "" and r["item"]["proc"] == "None" and \
           r["item"]["title"] == ""


def create_record(start, end, data=None, cnt=1, idle_sum=0, idle=False):
    if not data:
        data = start
    return {
        "start": parse_time(start),
        "end": parse_time(end),
        "duration": parse_time(end) - parse_time(start),
        "source": data.get("source", ""),
        "item": data,
        "cnt": cnt,
        "idle_sum": idle_sum,
        "idle": idle,
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


def get_name(entry, patterns, idle=False):
    proc = match_proc(entry.get("proc", ""), patterns)
    idle = "Idle: " if idle else ""
    return "{}{} {}".format(idle, proc, entry.get("title", ""))


def match_proc(name, patterns):
    for i in patterns["proc-names"]:
        if i["re"].search(name):
            return i["name"]
    return name


def get_machine(log_filepath):
    filename = os.path.basename(log_filepath)
    return filename.split('.')[-2]


def get_patterns():
    if os.path.exists(os.path.expanduser("~/stalker/patterns.json")):
        d = json.load(open(os.path.expanduser("~/stalker/patterns.json"), "r"))
        for k, v in d.items():
            for p in v:
                p["re"] = re.compile(p["re"])
        return d
    else:
        return {
            "proc-names": [],
            "proc-tags": [],
            "title-tags": []
        }


def analyze_tags(stream):
    d = {}
    tagged = datetime.timedelta()
    for i in stream:
        if i["tags"]:
            tagged += i["duration"]
        for t in i["tags"]:
            if t not in d:
                d[t] = {
                    "duration": datetime.timedelta(),
                    "idle": datetime.timedelta(),
                }
            # todo aggregate samples for tags
            if i["idle"]:
                d[t]["idle"] += i["duration"]
            else:
                d[t]["duration"] += i["duration"]
    return sorted(d.items(), key=lambda x: x[1]["duration"],
                  reverse=True), tagged


def print_tag_summary(summary, tagged, logged_time):
    print("Tagged: {} ({:.2f}%)".format(human_time_diff(tagged),
                                        (tagged / logged_time) * 100))
    print("-" * 10)
    print("{: <20}\t{: <12}\t{: <6}\t{: <10}\t{: <10}".format(
        "tag", "duration", "percent", "idle", "idle perc"))
    for t, v in summary:
        duration = v["duration"]
        perc = ((duration + v["idle"]) / logged_time) * 100
        print("{: <20}\t{: <12}\t{:.2f} %\t{: <12}\t{:.2f} %".format(
            t, human_time_diff(duration), perc, human_time_diff(v["idle"]),
            (v["idle"] / (v["idle"] + duration)) * 100))


if __name__ == '__main__':
    main()
