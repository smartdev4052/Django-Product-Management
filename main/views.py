import datetime as dt
from isodate import parse_duration
from datetime import datetime, timedelta, time
from main.forms import PageCreateForm, PageEditForm, DocumentDefaultCreateForm, DocumentDefaultEditForm
from django.contrib import messages
import json
from core.decorators import is_office
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from oauth2client.transport import request
from main.serializers import serialize_meet_model
import project
from project.models import Activity, Project, Meet, Task, Team, Document, DocumentDefault
from main.models import Page
from django.contrib.auth.models import User
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from django.contrib.auth.decorators import login_required
from google.oauth2 import service_account
from order.models import Order
from project.models import Invite, Project, Meet, Task
from googleapiclient.discovery import build


def mesibo_view(request):
    return render(request, 'main/meet/mesibo.html')

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def calendar_index_view(request):
    context = {}
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'credentials.json'

    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('calendar', 'v3', credentials=credentials)

    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')

    events_result = service.events().list(calendarId='c_3gkjm7oka2lloj4le429lpr2ig@group.calendar.google.com', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    context['credentials'] = events
    return render(request, 'main/calendar/index.html', context)

def google_credentials():
   

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    delegated_credentials = credentials.with_subject('info@legisly.com')
    service = build('calendar', 'v3', credentials=delegated_credentials)
    return service

"""
CALENDAR
"""


@login_required
def calendar_index_view(request):
    service = google_credentials()

    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')

    events_result = service.events().list(calendarId='sikler.sikler@gmail.com', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))

        print(start, event['summary'])

    context = {}
    context['events'] = events
    return render(request, 'main/calendar/index.html', context)


@login_required
def calendar_create_view(request):
    # Refer to the Python quickstart on how to setup the environment:
    # https://developers.google.com/calendar/quickstart/python
    # Change the scope to 'https://www.googleapis.com/auth/calendar' and delete any
    # stored credentials.

    event = {
        'summary': 'Google I/O 2015',
        'location': '800 Howard St., San Francisco, CA 94103',
        'description': 'A chance to hear more about Google\'s developer products.',
        'start': {
            'dateTime': '2021-12-29T13:00:00',
            'timeZone': 'Europe/Budapest',
        },
        'end': {
            'dateTime': '2021-12-29T17:00:00',
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

    service = google_credentials()
    event = service.events().insert(calendarId='c_3gkjm7oka2lloj4le429lpr2ig@group.calendar.google.com',
                                    conferenceDataVersion=1, body=event,).execute()
    print('Event created: %s' % (event.get('hangoutLink')))
    return HttpResponse('kész')




def index_view(request):
    if request.user.is_authenticated:
        user = request.user
        context = {}
        #HA sima user
        if request.user.profile.user_role == 1:
             meets = Meet.objects.filter(to_user=user)
             orders = Order.objects.filter(client__user = user)
             tasks = Task.objects.filter(to_user=user).exclude(status='COMPLETE')[0:5]
             projects = Project.objects.filter(client__user = user)
             invites= Invite.objects.filter(is_read=False, recipient=user)
             context['meets'] = meets 
             context['orders'] = orders
             context['tasks'] = tasks
             context['projects'] = projects
             context['invites'] = invites
        #ha ügyvéd
        elif request.user.profile.user_role == 2:
            pass
        
        return render(request, 'main/overview/index.html', context)
    else:   
        return redirect('shop:shop_index')

# PAGE 
@login_required
@is_office
def page_index_view(request):
    pages = Page.objects.all()
    context = {}
    context['pages'] = pages
    return render(request, 'main/page/index.html', context)


def page_detail_view(request, slug):
    page = Page.objects.filter(slug = slug).first()
    context = {}
    context['page'] = page
    return render(request, 'main/page/detail.html', context)

@login_required
@is_office
def page_create_view(request):
    if request.method == 'POST':
        form = PageCreateForm(request.POST)
        if form.is_valid():

            form.save()
            messages.success(request, 'Succesfully')
            return redirect('main:page_index')
    else:
        form = PageCreateForm()
    return render(request, 'main/page/create.html', {'form': form})

@login_required
@is_office
def page_edit_view(request, slug):
    page = Page.objects.filter(slug = slug).first()
    if request.method == 'POST':
        form = PageEditForm(request.POST, instance=page)
        if form.is_valid():

            form.save()
            messages.success(request, 'Succesfully')
            return redirect('main:page_index')
    else:
        form = PageEditForm(instance=page)
    return render(request, 'main/page/edit.html', {'form': form})

@login_required
@is_office
def page_delete_view(request, slug):
    page = Page.objects.filter(slug = slug).delete()
    messages.success(request, 'Succesfully deleted')
    return render(request, 'main/page/detail.html')


"""
DOCUMENT
"""
@login_required
def document_index_view(request):
    documents = DocumentDefault.objects.all()
    context = {}
    context['documents'] = documents
    return render(request, 'main/document/index.html', context)


def document_detail_view(request, id):
    document = DocumentDefault.objects.filter(id = id).first()
    context = {}
    context['document'] = document
    return render(request, 'main/document/detail.html', context)

@login_required
def document_create_view(request):
    user = request.user
    if request.method == 'POST':
        form = DocumentDefaultCreateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = user
            form.save()
            messages.success(request, 'Succesfully')
            return redirect('main:document_index')
    else:
        form = DocumentDefaultCreateForm()
    return render(request, 'main/document/create.html', {'form': form})

@login_required
def document_edit_view(request, id):
    document = DocumentDefault.objects.filter(id = id).first()
    if request.method == 'POST':
        form = DocumentDefaultEditForm(request.POST, instance=document)
        if form.is_valid():

            form.save()
            messages.success(request, 'Succesfully')
            return redirect('main:document_index')
    else:
        form = DocumentDefaultEditForm(instance=document)
    return render(request, 'main/document/edit.html', {'form': form, 'document': document})

@login_required
def document_delete_view(request, id):
    document = DocumentDefault.objects.filter(id = id).delete()
    messages.success(request, 'Succesfully deleted')
    return render(request, 'main/document/detail.html')

"""
MEET
"""

@login_required
def meet_index_view(request):
    user = request.user
    now = datetime.now()
    meets = Meet.objects.filter(to_user=user, project__archived = False).filter(meet_start__gte=now)

    data = [serialize_meet_model(i, meets)
            for i in meets]  # serialize to qs to obj

    context = {}
    context['meets'] = meets
    context['data'] = data
    return render(request, 'main/meet/index.html', context)


@login_required
def task_index_view(request):
    user = request.user
    # TODO: if archived the project.exclude(project) not show
    tasks = Task.objects.filter(to_user=user,project__archived = False).exclude(status='COMPLETE')
    context = {}
    context['tasks'] = tasks
    return render(request, 'main/task/index.html', context)


@login_required
def activity_index_view(request):
    user = request.user
    team = Team.objects.filter(user=user).values_list('project_id', flat=True)
    if user.profile.user_role == 1:
        activities = Activity.objects.filter(project__in=team).exclude(lawyer_mode=True)[0:200]
    elif user.profile.user_role == 2:
        activities = Activity.objects.filter(project__in=team)[0:200]

    context = {}
    context['activities'] = activities
    return render(request, 'main/activity/index.html', context)

@login_required
def activity_detail_view(request, id):
    user = request.user
    team = Team.objects.filter(user=user).values_list('project_id', flat=True)
    activity = Activity.objects.filter(id = id, project__in=team).first()
    Activity.objects.filter(id = id, project__in=team).update(is_read = True)
    context = {}
    context['activity'] = activity
    return render(request, 'main/activity/detail.html', context)

def time_slots(start_time, end_time, duration):
    x = []
    t = start_time
    while t <= end_time:
        yield t.strftime('%H:%M')
        t = (datetime.combine(datetime.today(), t) +
             timedelta(minutes=duration)).time()


def cal(request):
    start_time = dt.time(10, 35)
    end_time = dt.time(20, 35)
    duration = 15
    slots = list(time_slots(start_time, end_time, duration))

    return HttpResponse('dqw')


def calendly(request):
    return render(request, 'main/calendar/calendly.html')

# AJAX


def json_calendly_view(request):
    payload = {}
    if request.method == "GET":
        calendly_date = request.GET.get("calendly_date")
        print(calendly_date)

        # az adot dátum alapján lekérdezem az időponttokat

        # ellenőrzőm, hogy van e itt foglalt időpont és mennyi

        # visszaküldöm, a szabad időpontokat.

        start_time = dt.time(10, 35)
        end_time = dt.time(20, 35)
        duration = 60
        slots = list(time_slots(start_time, end_time, duration))
        payload['response'] = "True"
        payload['slots'] = slots
        # print(payload)

    return JsonResponse(payload)


"""
ERROR PAGES
"""


def handler_400_view(request, exception):
    return render(request, 'error/400.html', status=400)


def handler_403_view(request, exception):
    return render(request, 'error/403.html', status=403)


def handler_404_view(request, exception):
    return render(request, 'error/404.html', status=404)


def handler_500_view(request):
    return render(request, 'error/500.html', status=500)
