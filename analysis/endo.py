from endomondo.endomondo import MobileApi
from datetime import timezone
import datetime

def get_workouts(start, end, token):
    endomondo = MobileApi(auth_token=token)
    workouts = endomondo.get_workouts(before=end)

    data = []
    for w in workouts:
        w.start_time = w.start_time.replace(tzinfo=timezone.utc)
        if start > w.start_time:
            continue
        data.append(
            {
                "item": {
                    "title": "{} ({:.2f}km)".format(w.name, w.distance),
                },
                "start": w.start_time,
                "end": w.start_time + datetime.timedelta(seconds=w.duration),
                "duration": datetime.timedelta(seconds=w.duration),
                "tags": ["endomondo", "sport"],
                "source": "endomondo",
                "idle": False,
            })
    return data


if __name__ == '__main__':
    import sys
    import config

    now = datetime.datetime.now()
    if not config.endomondo_token:
        print("token not found")
        sys.exit(1)
    get_workouts(now + datetime.timedelta(days=-1), now, config.endomondo_token)
