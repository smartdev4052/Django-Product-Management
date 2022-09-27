from dateutil.parser import parse as dtparse
from datetime import datetime as dt
import json
from django.http import request
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from main.serializers import serialize_meet_model
from project.models import Project, Meet, Task
from django.contrib.auth.models import User
from datetime import datetime

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account




def google_credentials():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_credentials = credentials.with_subject('info@legisly.com')
    service = build('calendar', 'v3', credentials=credentials)
    return service


"""
CALENDAR API
"""
# TODO: a usereket be kell tenni


def calendar_index_view(calendar_id):
    service = google_credentials()

    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                          maxResults=20, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))

        print(start, event['summary'])

    #context = {}
    #context['events'] = events
    return events
    # return render(request, 'main/calendar/index.html', context)


def calendar_create_view(calendar_id, name, description, to_users, meet_start, meet_end, obj_id):
    # Refer to the Python quickstart on how to setup the environment:
    # https://developers.google.com/calendar/quickstart/python
    # Change the scope to 'https://www.googleapis.com/auth/calendar' and delete any
    # stored credentials.

    print('bet vok')
    print(name)
    print(description)
    print(to_users)
    print(meet_start)
    print(meet_end)

    _calendar_id = str(calendar_id)

    _name = str(name)
    _description = str(description)
    #_to_users = str(to_users)
    o_meet_start = str(meet_start)
    o_meet_end = str(meet_end)

    tmfmt = '%Y-%m-%dT%H:%M:%S.%fZ'
    _meet_start = dt.strftime(dtparse(o_meet_start), format=tmfmt)
    _meet_end = dt.strftime(dtparse(o_meet_end), format=tmfmt)

    event = {
        'summary': _name,
        'location': 'Budapest',
        'description': _description,
        'start': {
            'dateTime': _meet_start,
            'timeZone': 'Europe/Budapest',
        },
        'end': {
            'dateTime': _meet_end,
            'timeZone': 'Europe/Budapest',
        },

        "conferenceData": {
            "createRequest": {
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                },
                "requestId": "some-random-string"
            }
        },

        'attendees': [
            {'email': 'sikler.sikler@gmail.com'},

        ],

        'reminders': {
            'useDefault': True,
        },

    }

    # TODO: itt ki kell cserélni majd a id változóra
    service = google_credentials()
    event = service.events().insert(calendarId='c_3gkjm7oka2lloj4le429lpr2ig@group.calendar.google.com',
                                    conferenceDataVersion=1, body=event,).execute()
    print('Event created: %s' % (event.get('hangoutLink')))

    # Ha létrejön a meet akkor updateli a cuccost
    try:
        Meet.objects.filter(id=obj_id).update(url=event.get('hangoutLink'))
    except:
        print('Nem jött létre a meet.')

    return event
