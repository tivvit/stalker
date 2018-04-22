import datetime
import json
import os

from flask import Flask
from flask import request
from flask import render_template
from flask import redirect

import analysis
from analysis.analyze_day import human_time_diff
from analysis.analyze_day import load_stream
from analysis.analyze_day import process_stream
from analysis.analyze_day import get_name

app = Flask(__name__)
data_path = "/data/"


@app.template_filter()
def timediff(diff):
    return human_time_diff(diff)


@app.route("/")
def main():
    now = datetime.datetime.now()
    # working over midnight - want to see "today"
    if now.time() < analysis.config.morning:
        now -= datetime.timedelta(days=1)
    date = datetime.datetime.strftime(now, "%y-%m-%d")
    return redirect("{}".format(date), code=302)


@app.route("/<date>")
def main_date(date):
    day_filename = os.path.join(data_path, date)
    stream = load_stream(day_filename)
    next_day = datetime.datetime.strptime(date, "%y-%m-%d") + \
               datetime.timedelta(days=1)
    day_filename = os.path.join(data_path,
                                next_day.strftime("%y-%m-%d"))
    stream += load_stream(day_filename, only_morning=True)
    datetime.timedelta().total_seconds()
    if not stream:
        # todo
        print("No data found")
        return
    times = process_stream(stream)
    append_metadata(date, times)
    times = create_groups(times)
    times.sort(key=lambda x: x["start"])
    # todo detect sources
    # times = [i for i in times if i["duration"] > datetime.timedelta(seconds=2)]
    for i in times:
        i.update({
            "name": get_name(i["item"]) if "group" not in i else i["name"],
            "id": "{}$-${}".format(i.get("source", "Unknown "),
                                   i["start"].timestamp()),
        })
    # todo hotfix
    for i in times:
        if "group" in i:
            for g in i["group"]:
                g.update({
                    "name": get_name(g["item"]),
                    "id": "{}$-${}".format(g.get("source", "Unknown "),
                                           g["start"].timestamp()),
                })
    return render_template('index.html', data=times, date=date)


def append_metadata(date, times):
    filename = os.path.join(data_path,
                            "{}{}".format(date, ".metadata.json"))
    if not os.path.exists(filename):
        return
    metadata = json.load(open(filename, "r"))
    for i in times:
        src = i.get("source", "Unknown")
        if src not in metadata:
            continue
        timestamp = str(i["start"].timestamp())
        if timestamp in metadata[src]:
            i.update(metadata[src][timestamp])


def create_groups(times):
    last_desc = None
    out = []
    group = []
    for i in times:
        if "description" not in i and not last_desc:
            out.append(i)
        elif "description" not in i and last_desc:
            s = datetime.timedelta()
            for g in group:
                s += g["duration"]
            out.append({
                "start": group[0]["start"],
                "duration": s,
                "name": last_desc,
                "group": group,
            })
            last_desc = None
            group = []
            out.append(i)
        elif "description" in i and not last_desc:
            last_desc = i["description"]
            group = []
            group.append(i)
        elif i["description"] != last_desc:
            s = datetime.timedelta()
            for g in group:
                s += g["duration"]
            out.append({
                "start": group[0]["start"],
                "duration": s,
                "name": last_desc,
                "group": group,
            })
            last_desc = i["description"]
            group = []
            group.append(i)
        else:
            group.append(i)
    if group:
        s = datetime.timedelta()
        for g in group:
            s += g["duration"]
        out.append({
            "start": group[0]["start"],
            "duration": s,
            "name": last_desc,
            "group": group,
        })
    return out


@app.route("/hide", methods=["POST"])
def hide():
    data = request.json
    filename = os.path.join(data_path,
                            "{}{}".format(data["date"], ".metadata.json"))
    metadata = {}
    if os.path.exists(filename):
        metadata = json.load(open(filename, "r"))
    for i in data["items"]:
        source, timestamp = i.split("$-$")
        if source not in metadata:
            metadata[source] = {}
        if timestamp not in metadata[source]:
            metadata[source][timestamp] = {}
        metadata[source][timestamp].update({
            "hidden": True,
        })
    json.dump(metadata, open(filename, "w"))
    return ""


@app.route("/tags", methods=["POST"])
def tag():
    data = request.json
    filename = os.path.join(data_path,
                            "{}{}".format(data["date"], ".metadata.json"))
    metadata = {}
    if os.path.exists(filename):
        metadata = json.load(open(filename, "r"))
    for i in data["items"]:
        source, timestamp = i.split("$-$")
        if source not in metadata:
            metadata[source] = {}
        if timestamp not in metadata[source]:
            metadata[source][timestamp] = {}
        tags = set(metadata[source][timestamp].get("tags", []))
        for t in data.get("tags", []):
            if t.startswith("-"):
                e = t[1:]
                if e in tags:
                    tags.remove(e)
            else:
                tags.add(t)
        metadata[source][timestamp]["tags"] = list(tags)
    json.dump(metadata, open(filename, "w"))
    return ""


@app.route("/describe", methods=["POST"])
def describe():
    data = request.json
    filename = os.path.join(data_path,
                            "{}{}".format(data["date"], ".metadata.json"))
    metadata = {}
    if os.path.exists(filename):
        metadata = json.load(open(filename, "r"))
    for i in data["items"]:
        source, timestamp = i.split("$-$")
        if source not in metadata:
            metadata[source] = {}
        if timestamp not in metadata[source]:
            metadata[source][timestamp] = {}
        metadata[source][timestamp].update({
            "description": data["description"],
        })
    json.dump(metadata, open(filename, "w"))
    return ""


@app.route("/undescribe", methods=["POST"])
def undescribe():
    data = request.json
    filename = os.path.join(data_path,
                            "{}{}".format(data["date"], ".metadata.json"))
    metadata = {}
    if os.path.exists(filename):
        metadata = json.load(open(filename, "r"))
    for i in data["items"]:
        source, timestamp = i.split("$-$")
        if source not in metadata:
            metadata[source] = {}
        if timestamp not in metadata[source]:
            metadata[source][timestamp] = {}
        metadata[source][timestamp].pop("description", None)
    json.dump(metadata, open(filename, "w"))
    return ""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, threaded=True)
