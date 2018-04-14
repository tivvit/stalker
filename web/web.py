import datetime
import os

from flask import Flask
from flask import render_template

from analysis.analyze_day import human_time_diff
from analysis.analyze_day import load_stream
from analysis.analyze_day import process_stream
from analysis.analyze_day import get_name

app = Flask(__name__)


@app.template_filter()
def timediff(diff):
    return human_time_diff(diff)


@app.route("/")
def main():
    date = "18-04-14"
    day_filename = os.path.join("/data/", date)
    stream = load_stream(day_filename)
    next_day = datetime.datetime.strptime(date, "%y-%m-%d") + \
               datetime.timedelta(days=1)
    day_filename = os.path.join("/data/",
                                next_day.strftime("%y-%m-%d"))
    stream += load_stream(day_filename, only_morning=True)
    if not stream:
        # todo
        print("No data found")
        return
    times = process_stream(stream)
    times.sort(key=lambda x: x["start"])
    # todo detect sources
    times = [i for i in times if i["duration"] > datetime.timedelta(seconds=2)]
    for i in times:
        i.update({
            "name": get_name(i["item"])
        })
    return render_template('index.html', data=times)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, threaded=True)
