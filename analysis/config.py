import datetime
import os
from os.path import expanduser

import yaml

conf_file_path = os.path.dirname(os.path.realpath(__file__)) + "/config.yml"
base_path = expanduser("~/stalker/")
morning = datetime.time(hour=5)
toggl_api_key = ""

if os.path.exists(conf_file_path):
    print("Loading conf from {}".format(conf_file_path))
    conf = yaml.load(open(conf_file_path))
    if "toggl_api_key" in conf:
        toggl_api_key = conf.get("toggl_api_key", "")
