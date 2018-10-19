from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime
import os
import ciso8601


class Gcal(object):
    def __init__(self):
        self.service = self.get_service()

    def get_calendars(self):
        for c in self.service.calendarList().list(
                showHidden=True).execute().get("items", []):
            print(c.get("summary", ""), c.get("id", ""))

    def get_service(self):
        SCOPES = 'https://www.googleapis.com/auth/calendar'
        store = file.Storage(
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'credentials.json'))
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'client_secret.json'), SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('calendar', 'v3', http=creds.authorize(Http()))
        return service

    def events(self, calendars, start, end):
        data = []
        for cal in calendars:
            cal_name = self.service.calendarList().get(
                calendarId=cal).execute().get("summary", "")
            events_result = self.service.events().list(calendarId=cal,
                                                       timeMin=start,
                                                       timeMax=end,
                                                       maxResults=100,
                                                       singleEvents=True,
                                                       orderBy='startTime').execute()
            events = events_result.get('items', [])

            for event in events:
                data.append(self.convert_to_event(event, cal=cal_name))
        return data

    def get_sleep(self, sleep_cal, start, end):
        events = []
        events_result = self.service.events().list(
            calendarId=sleep_cal,
            timeMin=start,
            timeMax=end,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime').execute().get("items", [])
        if not events_result:
            return events
        for ev in events_result:
            events.append(self.convert_to_event(ev, cal="Sleep", idle=True))
        return events

    def add_tz(self, val):
        tz = datetime.datetime.utcnow().astimezone().tzinfo
        if not val.tzinfo:
            return val.replace(tzinfo=tz)
        return val

    def convert_to_event(self, cal_event, cal=None, idle=False):
        event_start = cal_event['start'].get('dateTime',
                                             cal_event['start'].get('date'))

        event_start = self.add_tz(ciso8601.parse_datetime(event_start))
        event_end = cal_event['end'].get('dateTime',
                                         cal_event['end'].get('date'))
        event_end = self.add_tz(ciso8601.parse_datetime(event_end))
        return {
            "item": {
                "title": cal_event.get("summary", ""),
            },
            "start": event_start,
            "end": event_end,
            "duration": event_end - event_start,
            "tags": ["gcal"] + ([cal] if cal else []),
            "source": "gcal",
            "idle": idle,
        }

    def create_event(self):
        event = {
            'summary': 'Google I/O 2015',
            'location': '800 Howard St., San Francisco, CA 94103',
            'description': 'A chance to hear more about Google\'s developer products.',
            'start': {
                'dateTime': '2015-05-28T09:00:00-07:00',
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': '2015-05-28T17:00:00-07:00',
                'timeZone': 'America/Los_Angeles',
            },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=2'
            ],
            'attendees': [
                {'email': 'lpage@example.com'},
                {'email': 'sbrin@example.com'},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        event = self.service.events().insert(calendarId='primary',
                                             body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))


if __name__ == '__main__':
    import config

    gcal = Gcal()

    tz = datetime.datetime.utcnow().astimezone().tzinfo
    today = datetime.datetime.utcnow().replace(minute=0, hour=0,
                                               second=0, tzinfo=tz)
    today_iso = today.isoformat()
    end = (today + datetime.timedelta(days=1)).isoformat()
    print(gcal.events(config.calendars, today_iso, end))
    print(gcal.get_sleep(config.sleep_calendar, today_iso, end))
