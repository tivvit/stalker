import datetime
import os
from os.path import expanduser

import yaml

conf_file_path = os.path.dirname(os.path.realpath(__file__)) + "/config.yml"
base_path = expanduser("~/stalker/")
morning = datetime.time(hour=5)
toggl_api_key = ""
endomondo_username = ""
endomondo_pass = ""
endomondo_token = ""
calendars = ["primary"]
sleep_calendar = ""

if os.path.exists(conf_file_path):
    print("Loading conf from {}".format(conf_file_path))
    conf = yaml.load(open(conf_file_path))
    if conf:
        if "toggl_api_key" in conf:
            toggl_api_key = conf.get("toggl_api_key", "")
        if "endomondo_username" in conf:
            endomondo_username = conf.get("endomondo_username", "")
        if "endomondo_pass" in conf:
            endomondo_pass = conf.get("endomondo_pass", "")
        if "endomondo_token" in conf:
            endomondo_token = conf.get("endomondo_token", "")
        if "calendars" in conf:
            calendars = conf.get("calendars", "")
        if "sleep_calendar" in conf:
            sleep_calendar = conf.get("sleep_calendar", "")
