from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime
import os
import ciso8601
import google.oauth2.credentials

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow


class Gfit(object):
    def __init__(self):
        self.service = self.get_service()

    def type(self, id):
        return {
            "9": "Aerobics",
            "10": "Badminton",
            "11": "Baseball",
            "12": "Basketball",
            "13": "Biathlon",
            "1": "Biking",
            "14": "Handbiking",
            "15": "Mountain biking",
            "16": "Road biking",
            "17": "Spinning",
            "18": "Stationary biking",
            "19": "Utility biking",
            "20": "Boxing",
            "21": "Calisthenics",
            "22": "Circuit training",
            "23": "Cricket",
            "106": "Curling",
            "24": "Dancing",
            "102": "Diving",
            "25": "Elliptical",
            "103": "Ergometer",
            "26": "Fencing",
            "27": "Football (American)",
            "28": "Football (Australian)",
            "29": "Football (Soccer)",
            "30": "Frisbee",
            "31": "Gardening",
            "32": "Golf",
            "33": "Gymnastics",
            "34": "Handball",
            "35": "Hiking",
            "36": "Hockey",
            "37": "Horseback riding",
            "38": "Housework",
            "104": "Ice skating",
            "0": "In vehicle",
            "39": "Jumping rope",
            "40": "Kayaking",
            "41": "Kettlebell training",
            "42": "Kickboxing",
            "43": "Kitesurfing",
            "44": "Martial arts",
            "45": "Meditation",
            "46": "Mixed martial arts",
            "2": "On foot",
            "108": "Other (unclassified fitness activity)",
            "47": "P90X exercises",
            "48": "Paragliding",
            "49": "Pilates",
            "50": "Polo",
            "51": "Racquetball",
            "52": "Rock climbing",
            "53": "Rowing",
            "54": "Rowing machine",
            "55": "Rugby",
            "8": "Running",
            "56": "Jogging",
            "57": "Running on sand",
            "58": "Running (treadmill)",
            "59": "Sailing",
            "60": "Scuba diving",
            "61": "Skateboarding",
            "62": "Skating",
            "63": "Cross skating",
            "105": "Indoor skating",
            "64": "Inline skating (rollerblading)",
            "65": "Skiing",
            "66": "Back-country skiing",
            "67": "Cross-country skiing",
            "68": "Downhill skiing",
            "69": "Kite skiing",
            "70": "Roller skiing",
            "71": "Sledding",
            "72": "Sleeping",
            "109": "Light sleep",
            "110": "Deep sleep",
            "111": "REM sleep",
            "112": "Awake (during sleep cycle)",
            "73": "Snowboarding ",
            "74": "Snowmobile",
            "75": "Snowshoeing",
            "76": "Squash",
            "77": "Stair climbing",
            "78": "Stair-climbing machine",
            "79": "Stand-up paddleboarding",
            "3": "Still (not moving)",
            "80": "Strength training",
            "81": "Surfing",
            "82": "Swimming",
            "84": "Swimming (open water)",
            "83": "Swimming (swimming pool)",
            "85": "Table tennis (ping pong)",
            "86": "Team sports",
            "87": "Tennis",
            "5": "Tilting (sudden device gravity change)",
            "88": "Treadmill (walking or running)",
            "4": "Unknown (unable to detect activity)",
            "89": "Volleyball",
            "90": "Volleyball (beach)",
            "91": "Volleyball (indoor)",
            "92": "Wakeboarding",
            "7": "Walking ",
            "93": "Walking (fitness)",
            "94": "Nording walking",
            "95": "Walking (treadmill)",
            "96": "Waterpolo",
            "97": "Weightlifting",
            "98": "Wheelchair",
            "99": "Windsurfing",
            "100": "Yoga",
            "101": "Zumba"
        }.get(str(id), "UNKNOWN")

    def get_service(self):
        SCOPES = [
            "https://www.googleapis.com/auth/fitness.location.read",
            "https://www.googleapis.com/auth/fitness.body.read",
            "https://www.googleapis.com/auth/fitness.activity.read",
        ]

        # flow = InstalledAppFlow.from_client_secrets_file(os.path.join(os.path.dirname(
        #         os.path.realpath(__file__)), 'client_secret.json'),
        #                                                  SCOPES)
        # credentials = flow.run_console()
        # return build('fitness', 'v1', credentials=credentials)

        store = file.Storage(
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'credentials_fit.json'))
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'client_secret.json'), SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('fitness', 'v1', http=creds.authorize(Http()))
        return service

    def events(self, start_time, time_end, tz=None):
        page_token = None
        data = []
        while True:
            events_result = self.service.users().sessions().list(
                userId="me",
                startTime=start_time,
                endTime=time_end,
                pageToken=page_token
            ).execute()
            data += list(map(
                lambda x: self.create_record(x, tz=tz),
                events_result.get('session', [])))
            if not events_result.get("hasMoreData", False):
                break
            page_token = events_result.get("nextPageToken", "")
        return data

    def create_record(self, data, tz=None):
        if not tz:
            tz = datetime.datetime.utcnow().astimezone().tzinfo
        event_end = datetime.datetime.fromtimestamp(
            int(data.get('endTimeMillis', "0")) / 1000).replace(tzinfo=tz)
        event_start = datetime.datetime.fromtimestamp(
            int(data.get('startTimeMillis', "0")) / 1000).replace(tzinfo=tz)
        return {
            "item": {
                "title": data.get('name', ""),
                "proc": self.type(data.get('activityType', 999))
            },
            "start": event_start,
            "end": event_end,
            "duration": event_end - event_start,
            "tags": ["sport", "gfit"],
            "source": "Gfit - {}".format(data.get('application', {}).get(
                'packageName', "")),
            "idle": False,
        }

    def get_ds(self):
        for i in self.service.users().dataSources().list(
                userId="me").execute().get("dataSource", []):
            print(i.get("dataStreamId", ""))

    def get_heart_rate(self):
        # last hour
        print(self.service.users().dataSources().datasets().get(
            userId="me",
            dataSourceId="derived:com.google.heart_rate.bpm:com.google"
                         ".android.gms:merge_heart_rate_bpm",
            datasetId="{}-{}".format(
                (round(datetime.datetime.utcnow().timestamp() - 60 * 60) *
                 (10 ** 9)),
                round(datetime.datetime.utcnow().timestamp() * (10 ** 9))),
        ).execute())


if __name__ == '__main__':
    fit = Gfit()
    tz = datetime.datetime.utcnow().astimezone().tzinfo
    today = datetime.datetime.utcnow().replace(minute=0, hour=0,
                                               second=0, tzinfo=tz)
    today_iso = today.isoformat()
    end = (today + datetime.timedelta(days=1)).isoformat()
    print(fit.events(today_iso, end))
