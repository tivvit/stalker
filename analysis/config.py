from os.path import expanduser

import datetime

base_path = expanduser("~/stalker/")

mapping = {
    "chrome": "chrome",
    "terminal": "terminal",
    "pycharm": "pycharm",
}

morning = datetime.time(hour=5)
