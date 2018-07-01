import datetime

import ciso8601

from TogglPy import Toggl


def toggl(start, end, api_key):
    toggl = Toggl()
    toggl.setAPIKey(api_key)
    data = []

    for w in toggl.getWorkspaces():
        w_name = w.get("name", "")
        w_id = w.get("id", "")
        if not w_id:
            continue

        for r in toggl.getDetailedReport({
            'workspace_id': w_id,
            'since': start.strftime("%Y-%m-%d"),
            'until': end.strftime("%Y-%m-%d"),
        }).get("data", []):
            data.append({
                "item": {
                    "title": r.get("description", "").strip(),
                },
                "start": ciso8601.parse_datetime(r.get("start", "")),
                "end": ciso8601.parse_datetime(r.get("end", "")),
                "duration": datetime.timedelta(milliseconds=r.get("dur", 0)),
                "tags": r.get("tags", []) + [r.get("client", ""),
                                             r.get("project", ""),
                                             w_name],
                "source": "toggl",
                "idle": False,
            })
    return data
