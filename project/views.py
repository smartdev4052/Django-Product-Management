from os import name
from django import forms
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from account.models import Profile
from client.models import Client
from order.models import Order
from project.models import Activity, Invite, Meet, Note, Project,DocumentDefault, ProjectForm,Document, Team, Task, Message, File, TeamType, ProjectFormDefault
from project.forms import MeetCreateForm, NoteCreateForm,DuplicateForm,ProjectCloseForm,EditResponsibleForm,EditParticipantForm, TaskResponsibleForm,EditForm,DocumentEditForm,DocumentCreateForm,CreateForm, NoteEditForm,MeetInviteForm, MeetEditForm, NoteFormCreateForm, ProjectEditForm, NoteMeetCreateForm, NoteTaskCreateForm, ProjectCreateAdminForm, ProjectCreateForm, TaskCreateForm, TaskEditForm, TeamCreateForm, TeamCreateWithBookForm, TeamEditForm, TeamInviteForm, MessageCreateForm, FileCreateForm, FileEditForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from notification.models import Notification
import uuid
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from core.decorators import is_lawyer
from django.template.loader import render_to_string
from django.core.mail import send_mail
from smtplib import SMTPException
from project.calendar import calendar_index_view, calendar_create_view
from django.utils.translation import ugettext_lazy as _
from core.utils import SignalSystem
from django.contrib.sites.shortcuts import get_current_site #domaint innen szerzem meg
from datetime import timedelta

#pdf generate
from django.http import HttpResponse
from django.views.generic import View
from .process import html_to_pdf 

class GeneratePdf(View):
     def get(self, request, *args, **kwargs):
        # getting the template
        document_id = kwargs.get('id', None)
        document = Document.objects.filter(id = document_id).first()
        context = {}
        context['obj'] = request.user 
        context['document'] = document
        pdf = html_to_pdf('document/result.html', context)
        # rendering the template
        return HttpResponse(pdf, content_type='application/pdf')


#google
from oauth2client.transport import request
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from django.contrib.auth.decorators import login_required
from google.oauth2 import service_account



# Check permission function




def permission_check(user, project):
    team = Team.objects.filter(
        user=user, active=True, project=project).exists()
    if team:
        team_role = Team.objects.filter(user=user, active=True, project=project).first()
        return team_role
    if team == False:
        raise PermissionDenied

# Check Lawyer permission function


def permission_check_lawyer(user, project):
    team = Team.objects.filter(
        user=user, active=True, project=project, staff=True).exists()
    if team == False:
        raise PermissionDenied


@login_required
def invite_index_view(request):
    user = request.user
    invites = Invite.objects.filter(recipient=user).exclude(is_read=True)
    context = {}
    context['invites'] = invites
    return render(request, 'invite/index.html', context)


@login_required
def invite_accept_view(request, project_id):
    user = request.user
    project = Project.objects.filter(id=project_id).first()
    # Check invite is okay
    invited_user = Invite.objects.filter(
        recipient=user, project=project).first()

    # Check invited user in Team -- megnézem hogy létezik e a user
    team = Team.objects.filter(
        user=user, active=False, project=project).exists()
    # If not in the team -> 403
    if team == False or invited_user is None:
        raise PermissionDenied


    #Megkeresem a projektben a megrendelőt
    customer = Team.objects.filter(project = project, customer = True).first()

   
    
    #google calendar create
    try:
        meet_start = str(invited_user.meet_start)
        meet_end = str(invited_user.meet_end)
        meet_start_raw = datetime.strptime(meet_start, '%Y-%m-%d %H:%M:%S+00:00')
        meet_end_raw = datetime.strptime(meet_end, '%Y-%m-%d %H:%M:%S+00:00')

        meet_start_raw = str(meet_start_raw).replace('+00:00', 'Z').replace(' ', 'T')
        meet_end_raw = str(meet_end_raw).replace('+00:00', 'Z').replace(' ', 'T')

        # megvan a dátum normál formátumba idpontot létrehozatom
        event = {
                'summary': str(project.name),
                'location': '',
                'description': str(project.description),
                'start': {
                    'dateTime': meet_start_raw,
                    'timeZone': 'Europe/Budapest',
                },
                'end': {
                    'dateTime': meet_end_raw,
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
                    {'email': request.user.email},

                ],

                'reminders': {
                    'useDefault': True,
                },

            }

        event_link = ''

        #if request.user.profile.calendar_id:
        try:
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            SERVICE_ACCOUNT_FILE = 'credentials.json'
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            delegated_credentials = credentials.with_subject('info@legisly.com')
            service = build('calendar', 'v3', credentials=delegated_credentials)

            #TODO: ide jöjjön be az ügyvéd id-ja ha nincs akkor el se inditsa ezt a szálat request.user.profile.calendar_id
            event = service.events().insert(calendarId=request.user.profile.calendar_id,
                                            conferenceDataVersion=1, body=event,).execute()
            #print('Event created: %s' % (event.get('hangoutLink')))
            event_link = event.get('hangoutLink')
            event_id = event.get('id')
        except:
            messages.warning(request, _('Error with API. Please add manually the event to Calendar (bad calendar ID in profile)'))
            return redirect('project:project_detail', project_id)


        try:
        # Add ME to meet
            meet = Meet.objects.create(name = project.name, url = event_link, google_calendar_id = event_id,from_user = user, project = project, meet_start= meet_start, meet_end=meet_end)
            Meet.objects.get(id=meet.id).to_user.add(user)
            # ha van customer és időpont akkor a customert hozzávonom az ügyhöz
            if customer:
                Meet.objects.get(id=meet.id).to_user.add(customer.user)
                SignalSystem.notification(request.user, (request.user.first_name + ' ' + request.user.last_name), customer.user, _(f"{request.user.first_name} {request.user.last_name} {_('invited you to a consultation on')} {meet.meet_start}. {_('Case:')} {project.name}."), 'INFO', '')
        except:
            pass

    except:
        pass
       
    # Change active false to active true
    try:
        #Ha ügyvéd van meghívva akkor 2 es user_role-t kap
        team_lawyer = Team.objects.filter(user=user, project=project).first()
        if request.user.profile.user_role == 2:
            Team.objects.filter(user=user, project=project).update(active=True, staff=True, role='2')
        else:
            Team.objects.filter(user=user, project=project).update(active=True)

        if project.responsible_user:
            #ha már van responsible user
            pass
        else:
            Project.objects.filter(id=project_id).update(responsible_user=user)

        Invite.objects.filter(
            recipient=user, project=project).update(is_read=True)
    except:
        # TODO: error handling
        pass

    """
    Attach to Task, Form, Document added in 2022.01
    """
    #Fontos leelenőrizin ohgy user obj megvna e mar vagy még csak új feéjaszánló
    #invited_obj = Invite.objects.filter(recipient=user, project=project).first()
    #if invited_obj

    for task in invited_user.task.all():
        Task.objects.get(id=task.id).to_user.add(request.user)

    for form in invited_user.project_form.all():
        ProjectForm.objects.get(id=form.id).to_user.add(request.user)

    for meet in invited_user.meet.all():
        Meet.objects.get(id=meet.id).to_user.add(request.user)

    # get team type after updateted active
    team_member = Team.objects.filter(
        user=user, project=project, active=True).first()
    
    if team_member:
        # Form search and create

        """
        default_form = ProjectFormDefault.objects.filter(
            team_type=team_member.team_type)
        for default in default_form:
            obj = ProjectFormDefault.objects.get(id=default.id)
            now = datetime.now()
            add_day = int(obj.start_date_plus_day)
            due_date = now + timedelta(days=add_day)
            project_form_obj = ProjectForm.objects.create(name=f'{obj.name} form - {project.name}',
                                        form_schema=obj.default_schema, form_meta=obj.default_meta, project=project, start_date=now , due_date=due_date)
            project_form_obj.to_user.add(user)
            # majd itt kell hozzáadni hogy many to many hozzáadja a team typot -- elv ez kész
        """
        

    # Activity
    Activity.objects.create(project=project, name=_("Joined to project"),
                            description=f'{request.user.first_name} {request.user.last_name} {_("have accepted to collaborate on")} {project.name}')

    return redirect('project:project_detail', project_id)


@login_required
def invite_decline_view(request, project_id):
    user = request.user
    project = Project.objects.filter(id=project_id).first()
    # ezzel tudom leelenőrizni, hogy stimelnek e a userek telejsen
    invited_user = Invite.objects.filter(
        recipient=user, project=project).first()

    # Check team is exist
    team = Team.objects.filter(
        user=user, active=False, project=project).exists()

    #if team == False or invited_user is None:
        #raise PermissionDenied

    project = Project.objects.filter(id=project_id).first()
    try:
        Team.objects.filter(user=user, project=project).delete()
        Invite.objects.filter(recipient=user, project=project).delete()
        # Remove lawyer from order (for calc system)
        order_object = Order.objects.filter(id=project.order_number).first()
        order_object.lawyer.remove(user)
    except:
        # TODO: error handling
        pass


     # Activity
    Activity.objects.create(project=project, name=_("Declined invitation"), description=f'{user.first_name} {user.last_name} {_("have declined to collaborate on")} {project.name}')

    return redirect('project:invite_index')


@login_required
def project_index_view(request):
    user = request.user
    context = {}
    if user.profile.user_role == 1:
        projects = Team.objects.filter(user=user, project__archived = False)
        context['projects'] = projects
        return render(request, 'project/my_project.html', context)
    elif user.profile.user_role == 2:
        projects = Team.objects.filter(user=user)
        context['projects'] = projects
        return render(request, 'project/my_project.html', context)
    elif user.profile.user_role == 3:
        projects = Project.objects.all()
        context['projects'] = projects
        return render(request, 'project/index.html', context)


@login_required
def project_create_view(request, client_id, product_id, order_id):
    user = request.user
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = user
            obj.save()

            project = Project.objects.filter(id=obj.id).first()

            try:
                created = Team.objects.create(
                    email=user.email, user=user, project=project, role=3, staff=True, active=True, is_removable=False)

                created2 = Team.objects.create(
                    email=obj.client.user.email, user=obj.client.user, project=project, role=2, active=True, is_removable=False)
            except:
                # TODO: error handling
                pass

            if created and created2:
                Order.objects.filter(id=order_id).update(active=True)
                return redirect('project:project_index')
            else:
                # TODO: error handling
                pass
                print('végzetes hiba törölni a cuccost és ujra létrehozatni ha')

        else:
            print('Form invalid')

    else:
        form = ProjectCreateForm()
        form.fields['client'] = forms.ModelChoiceField(
            Client.objects.filter(id=client_id), initial={'client_id': client_id}, label=_('Client'))

    return render(request, 'project/create.html', {'form': form})


@login_required
def project_create_admin_view(request):
    if request.method == 'POST':
        form = ProjectCreateAdminForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, _("Succesfully saved!"))
            return redirect('project:project_index')
    else:
        form = ProjectCreateAdminForm()
    return render(request, 'project/create_admin.html', {'form': form})


@login_required
def project_detail_view(request, id):
    #xxx = ProjectFormDefault.objects.all()
    user = request.user
    project = get_object_or_404(Project, id=id, archived = False, closed= False)

    # Check permission
    x = permission_check(user, project)

    notes = Note.objects.filter(project=project, type='NOTE')
    activities = Activity.objects.filter(
        project=project, lawyer_mode=False).order_by('-created_at')[0:15]
    context = {}
    context['project'] = project
    context['notes'] = notes
    context['activities'] = activities
    context['x'] = x
    #context['xxx'] = xxx
    return render(request, 'project/detail.html', context)


@login_required
def project_edit_view(request, project_id):
    user = request.user
    project = Project.objects.filter(id = project_id).first()

    if request.method == 'POST':
        form = ProjectEditForm(request.POST,instance=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, _('Succesfully saved'))
                # eredeti
            return redirect('project:project_index')
        else:
            print('Form invalid')

    else:
        form = ProjectEditForm(instance=project)

    return render(request, 'project/edit.html', {'form': form, 'project':project})


@login_required
def project_close_view(request, project_id):
    user = request.user
    project = Project.objects.filter(id = project_id).first()
    permission_check(user, project)

    if request.method == 'POST':
        form = ProjectCloseForm(request.POST,instance=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.closed = True
            obj.save()

            # Update order status
            try:
                Project.objects.filter(id=project_id).update(closed = True, archived = True)
                Order.objects.filter(project = project).update(status = 'CLOSED')
            except:
                pass
            messages.success(request, _('Succesfully closed'))
                # eredeti
            return redirect('project:project_index')
        else:
            print('Form invalid')

    else:
        form = ProjectCloseForm(instance=project)

    return render(request, 'project/close.html', {'form': form, 'project':project})

@login_required
def project_archive_view(request, project_id):
    user = request.user
    project = Project.objects.filter(id = project_id).first()
    permission_check(user, project)

    # Update order status
    try:
        Project.objects.filter(id=project_id).update(archived = True)
        Order.objects.filter(project = project).update(status = 'ARCHIVED')
        messages.success(request, _('Project archived'))
    except:
        pass

    return redirect('project:project_index')


@login_required
def project_unarchive_view(request, project_id):
    user = request.user
    project = Project.objects.filter(id = project_id).first()
    if request.user.profile.user_role != 3:
        permission_check(user, project)
    
    # Update order status
    try:
        Project.objects.filter(id=project_id).update(archived = False, closed = False)
        Order.objects.filter(project = project).update(status = 'IN_PROGRESS')
        messages.success(request, _('Project unarchived'))
    except:
        pass

    return redirect('project:project_index')


"""
TEAM
"""


@login_required
def project_team_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False,closed = False)
    teams = Team.objects.filter(project=project).exclude(role=3)
    customer = Team.objects.filter(project=project, user=user).first()

    print(customer)

    # Check permission
    x = permission_check(user, project)

    context = {}
    context['project'] = project
    context['teams'] = teams
    context['customer'] = customer
    context['x'] = x
    return render(request, 'team/index.html', context)


@login_required
# admin meghivja az embereit akik supervisorok
def project_team_create_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    context = {}
    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            user_obj = User.objects.get(username=user)

            # megnézi hogy hozzá van e már adva, ha igen akkor nem engedi ujra hozzáadni
            team = Team.objects.filter(user=user_obj).filter(
                project=project_id).exists()
            if(team):
                print('létezik már és redirect')
                messages.warning(
                    request, _('Already added the team. Please another people'))
                # eredeti
                return redirect('project:project_team_create', project_id)
                # return redirect('project:project_team_index', project_id) #eredeti
            else:
                obj = form.save(commit=False)
                obj.token = None
                obj.email = user_obj.email
                obj.project = project
                obj.is_removable = False  # is_removable
                obj.role = 2  # role #role'EDITOR'
                obj.staff = True
                obj.save()
                # form.save() # elv ez nem kell
                messages.success(request, _('Invite send!'))

                try:
                    # Invite
                    Invite.objects.create(sender=request.user, sender_display_name='Legisly system', recipient=user,
                                          action=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}', description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}.', project=project)

                    # Activity
                    Activity.objects.create(project=project, name=_('Invite new people'),
                                            description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}')

                except:
                    # TODO: error handling
                    pass

                context['project'] = project
                context['user_obj'] = user_obj
                context['sender'] = request.user
                context['DOMAIN'] = get_current_site(request)
                #user.email
                SignalSystem.email(user_obj.email, _("You have been invited to collaborate in a legal case"), 'email_project_invite.html', context)

                # Update order status
                try:
                    Order.objects.filter(project = project).update(status = 'IN_PROGRESS')
                except:
                    pass

                return redirect('project:project_index')
    else:
        form = TeamCreateForm()
        form.fields['user'] = forms.ModelChoiceField(
            Profile.objects.filter(user_role=2).exclude(user=request.user), label=_("User"))
    return render(request, 'team/office_invite.html', {'form': form, 'project': project})


@login_required
# TODO:
# Ugyanaz mint a sima meghivás csak ez dátummal megy.
def project_team_book_create_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)

    if request.method == 'GET':
        order_id = request.GET.get('order_id')
        order = Order.objects.filter(id=order_id).first()
    else:
        order = None

    if request.method == 'POST':
        form = TeamCreateWithBookForm(request.POST)
        order_id = request.GET.get('order_id')
        if form.is_valid():
            user = form.cleaned_data.get('user')
            meet_start = form.cleaned_data.get('meet_start')
            meet_end = form.cleaned_data.get('meet_end')

            user_obj = User.objects.get(username=user)

            # Check user is already added
            team = Team.objects.filter(user=user_obj).filter(
                project=project_id).exists()
            customer = Team.objects.filter(
                project=project_id, customer=True).first()

            # if already added
            if(team):
                messages.warning(
                    request, _('Already added the team. Please another people'))
                return redirect('project:project_team_create', project_id)

            else:
                obj = form.save(commit=False)
                obj.token = None
                obj.email = user_obj.email
                obj.project = project
                obj.is_removable = False  # is_removable
                obj.meet_start = meet_start
                obj.meet_end = meet_end
                obj.role = 2  # role #role'EDITOR'
                obj.staff = True
                obj.save()
                messages.success(request, _('Invite send!'))

                try:

                    # add lawyer to order for slot calc
                    order_obj = Order.objects.filter(id=order_id).first()
                    order_obj.lawyer.add(user)

                    # Invite
                    Invite.objects.create(sender=request.user, meet_start=meet_start, meet_end=meet_end, sender_display_name=_('Legisly system'), recipient=user,
                                          action=f'{_("Invited you for")} {project.name} - by Legisly Assistant', description=f'{_("Please join the project!")}', project=project)


                    # Activity
                    Activity.objects.create(project=project, name=_('Invite new people'),
                                            description=f'{_("The Legisly office invite for this project")}: {project.name}.')
                except:
                    # TODO:error handling
                    pass

                return redirect('project:project_index')
    else:
        form = TeamCreateWithBookForm()
        form.fields['user'] = forms.ModelChoiceField(
            Profile.objects.filter(user_role=2).exclude(user=request.user), label=_('Lawyer'))

    return render(request, 'team/office_invite.html', {'form': form, 'order': order, 'project': project})


@login_required
def project_team_edit_view(request, project_id, id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    team = get_object_or_404(Team, project=project_id, id=id)
    if request.method == 'POST':
        form = TeamEditForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect('project:project_team_index', project_id)
    else:
        form = TeamEditForm(instance=team)
    return render(request, 'team/edit.html', {'form': form, 'project': project})


"""
EZ AKKOR VAN HA A SIMA USER HÍV MEG, TODO: MAJD TÖRÖLNI AMI NEM KELL RÉSZ
"""


@login_required
def project_team_invite_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    if request.method == 'POST':
        form = TeamInviteForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            # user lecsipem a formbol küldésnél
            role = form.cleaned_data.get('role')
            #team_type_id = form.cleaned_data.get('team_type').id # ha használjuk ezt a faszomat
            #team_type_obj = TeamType.objects.get(id=team_type_id)# ha használjuk ezt a faszomat
            #print(team_type_obj)

            role_name = None
            if(role):
                if(role == '1'):
                    role_name = 'Editor'
                elif(role == '2'):
                    role_name = 'Reader'

            # Tiltott email címek
            lawyer_email = Profile.objects.filter(user__email = email, user_role=2).exists()
            if email == 'info@legisly.com' or email == 'office@legisly.com' or lawyer_email == True:
                messages.warning(request, _('The email is not useable or you try invite lawyer...'))
                return redirect('project:project_team_index', project_id)

            # Object from cleaned data
            # team objektet megkeresem megnézem ha tagja már a csapatnak
            team_obj = Team.objects.filter(
                email=email, project=project).exists()
            user_obj = User.objects.filter(
                email=email).exists()  # user objektet megkeresem
            token = uuid.uuid4()

            # Végnézem az ügyfelek között megvan e ez az email ha megvan akkor értesitő megy neki plustz beillesztem userkent ha nem akkor
            # megy ki neki az emial és beiilesztem üresjként majd emaille lregisztrálva aktivalodik

            if(team_obj):
                print('------------------')
                print('Létezik a team obj')
                print('------------------')
                print('Már jelenleg a csapat tagja visszairémnyités warning üzivel')
                messages.warning(
                    request, _('User is already in your team! Please select another e-mail!'))
                return redirect('project:project_team_index', project_id)

            if(user_obj):
                print('------------------')
                print('Létezik a user obj tehát küldeni neki meghívot')
                print('------------------')
                # adott user kapjon meghívot és  itt ha rakattol akkor valtozzon aktivra a dolog ha pedig elutasitja
                # akkor törlödjön a meghívása
                # get_or_create megoldfani!!!!
                user = User.objects.get(email=email)
                # team_type=team_type_obj ha szűkség lesz rá betenni
                obj, created = Team.objects.get_or_create(
                    email=user.email,
                    project=project,
                    user=user,
                    role=role,
                    token=None
                )

                messages.success(request, _('Invite sent succesfully!'))

                try:
                    # Invite
                    Invite.objects.create(sender=request.user, sender_display_name='Legisly system', recipient=user,
                                          action=f'{_("Invited you for")} {project.name}', description=f'{_("You have been invited to collaborate in a legal case")}{role}', project=project)

                    # Activity
                    Activity.objects.create(project=project, name=_('Invite new people'),
                                            description=f'{_("The Client invite")} ({email}) {_("with role:")} {role_name} {_("for this project:")} {project.name}.')
                except:
                    # TODO: error handling
                    pass

                
                context['project'] = project
                context['user_obj'] = user
                context['sender'] = request.user
                context['DOMAIN'] = get_current_site(request)
                #user.email
                SignalSystem.email(user.email, _("You have been invited to collaborate in a legal case"), 'email_project_invite.html', context)

                return redirect('project:project_team_index', project_id)
            else:
                print('------------------')
                print('Egyáltalán nincs a rendszerben a User emailes meghívó')
                print('------------------')
                # team_type=team_type_obj ezt majd betenni ha szűkség lesz rá
                obj, created = Team.objects.get_or_create(
                    email=email,
                    project=project,
                    role=role,
                    token=str(token)
                )

                messages.success(request, _('The invite sent successfully!'))

                # Activity
                Activity.objects.create(project=project, name=_('Invite new people'),
                                        description=f'{_("The client sent invite email for")} ({email}) {_("with role:")} {role_name} {_("for this project:")} {project.name}.')

                
                # Email
                context[''] = created
                context['project'] = project
                context['user_obj'] = user
                invite_link = f'https://app.legisly.com/register/invite/{token}'
                context['invite_link'] = invite_link
                context['sender'] = request.user
                context['DOMAIN'] = get_current_site(request)
                SignalSystem.email(email, _("You have been invited to collaborate in a legal case"), 'email_project_invite.html', context)

                return redirect('project:project_team_index', project_id)
        else:
            pass
    else:
        form = TeamInviteForm()
        # form.fields['type'] = forms.ModelChoiceField(TeamType.objects.all()) #TODO: ki kell tlaálni mi alapján szűrjön mert ha itt termék és a termék megszünik baszhatjuk vagyátmegy mert proul a rendszer

    return render(request, 'team/invite.html', {'form': form, 'project': project})


def project_team_invite_delete_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    team_obj =  Team.objects.filter(id = id, project = project).first()
    context = {}
    # Check permission
    x = permission_check(user, project)
    if x.customer == True or x.staff == True:
        try:
 
            Invite.objects.filter(project = project, recipient = team_obj.user).delete()
            Team.objects.filter(id = id, project = project).delete()
            Activity.objects.create(project=project, name=_('Deleted invitation'),
                                        description=f'{_("Deleted invitation by")} ({user.first_name} {user.last_name}) {_("for this project:")} {project.name}.')

            messages.success(request, _('The invite is deleted!'))
            return redirect('project:project_team_index', project_id)
        except:
            messages.warning(request, _('The invite is NOT deleted!'))
            return redirect('project:project_team_index', project_id)

        

        #SignalSystem.activity(project, _("Deleted invitation"), f'{_("Deleted invitation")} {_("by:")} {user.first_name} {user.last_name} {_("for this project:")} {project.name}.', user, ''):

    else:
        raise PermissionDenied


"""
DOCUMENT
"""
def project_document_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)
    documents = Document.objects.filter(project = project)
    context['documents'] = documents
    context['project'] = project
    return render(request, 'document/index.html', context)

def project_document_create_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    # Check permission
    permission_check(user, project)
    context = {}
    context['project'] = project
    default_documents = DocumentDefault.objects.all()

    return render(request, 'document/create.html', {'project': project, 'default_documents':default_documents})


    """
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    
    # Check permission
    permission_check(user, project)
    context = {}
    context['project'] = project
    if request.method == 'POST':

        form = DocumentCreateForm(request.POST)
        if form.is_valid():
            default_document_id = form.cleaned_data.get('default_document')
            default_document_obj = DocumentDefault.objects.filter(name = default_document_id).first() # a büdös kurva istenéé faszáér nem jó az ID val
            document = Document.objects.create(project = project, from_user = user, content=default_document_obj.content, name = default_document_obj.name)
            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_document_index', project_id)

    else:
        form = DocumentCreateForm()
    return render(request, 'document/create.html', {'form': form, 'project': project})
    """

def project_document_detail_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    document = Document.objects.filter(id = id).first()
    context = {}
    context['project'] = project
    context['document'] = document
    return render(request, 'document/detail.html', context) 

def project_document_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    document = Document.objects.filter(id = id).first()
    form_qs = ProjectForm.objects.filter(project = project)
    x = ProjectForm.objects.filter(id=42).first()
    context = {}
    context['project'] = project
    context['document'] = document
    context['form_qs'] = form_qs
    permission_check(user, project)

    if request.method == 'POST':

        form = DocumentEditForm(request.POST, instance=document)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_document_index', project_id)

            """
            try:
                # Activity create
                Activity.objects.create(project=project, user=user, name=_("Edit note"),
                                        description=f'{user.first_name} {user.last_name} _("edited the note:") {note.name} in {project.name}')
            except:
                # TODO: error handling
                pass
            """

    else:
        form = DocumentEditForm(instance=document)
    return render(request, 'document/edit.html', {'form': form, 'document': document, 'project': project, 'form_qs':form_qs, 'x':x})



def project_document_delete_view(request, project_id, id):
    pass
   


"""
NOTES
"""


@login_required
def project_note_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    x = permission_check(user, project)

    notes = Note.objects.filter(
        project=project, type='NOTE').exclude(lawyer_mode=True)
    file_qs = File.objects.filter(Q(project=project, file_type='NOTE', lawyer_mode=False) and Q(
        project=project, file_type='NOTE', lawyer_mode=False))
    context = {}
    context['notes'] = notes
    context['project'] = project
    context['file_qs'] = file_qs
    context['x'] = x
    return render(request, 'note/index.html', context)


@login_required
def project_note_create_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    
    team_qs = Team.objects.filter(project = project, active = True).exclude(role='3')

    if request.method == 'POST':
        form = NoteCreateForm(request.POST)
        if form.is_valid():
            private = form.cleaned_data.get('private')
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.type = 'NOTE'
            obj.save()

            if private == False:
                try:
                    # Activity create 
                    Activity.objects.create(project=project, user=user, name=_("Note created"),
                                            description=f'{user.first_name} {user.last_name} {_("added a new public note on")} {project.name}')
                except:
                    # TODO: error handling
                    pass

                #Email send
                context['note'] = obj
                context['DOMAIN'] = get_current_site(request)
                for team_obj in team_qs:
                    context['team_obj'] = team_obj
                    SignalSystem.email(team_obj.user.email, _("New note has been added"), 'email_note.html', context)


            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_note_index', project_id)
    else:
        form = NoteCreateForm()
    return render(request, 'note/create.html', {'form': form, 'project': project})


@login_required
def project_note_create_file_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    note = Note.objects.filter(id=id).first()
    if request.method == 'POST':
        #  megvizsgálom ha van e get paraméterbe task note
        task_id = request.GET.get('task_id')
        #  megvizsgálom ha van e get paraméterbe meet note
        meet_id = request.GET.get('meet_id')
        #  megvizsgálom ha van e get paraméterbe meet note
        form_id = request.GET.get('form_id')
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.uploaded_by = request.user
            obj.project = project
            obj.note = note
            if(task_id):
                try:
                    obj.file_type = 'TASK_NOTE'
                    obj.task = Task.objects.get(id=task_id)
                except:
                    # TODO: error trigger berakni
                    obj.file_type = 'TASK_NOTE'

            if(meet_id):
                try:
                    obj.file_type = 'MEET_NOTE'
                    obj.meet = Meet.objects.get(id=meet_id)
                except:
                    # TODO: error trigger berakni
                    obj.file_type = 'MEET_NOTE'

                
            if(form_id):
                try:
                    obj.file_type = 'FORM_NOTE'
                    obj.project_form = ProjectForm.objects.get(id=form_id)
                except:
                    # TODO: error trigger berakni
                    obj.file_type = 'FORM_NOTE'

            # 2022.01.03 lett betéve ez
            else:
                try:
                    obj.file_type = 'NOTE'
                except:
                    # TODO: error trigger berakni
                    obj.file_type = 'NOTE'

            obj.save()
            form.save()
            messages.success(request, _('Succesfully saved!'))

            try:
                # Activity create 
                Activity.objects.create(project=project, user=user, name=_("Upload new file to note"),
                                        description=f'{user.first_name} {user.last_name} {_("uploaded a new file to a public note on")} {project.name}')
            except:
                # TODO: error handling
                pass

            if(task_id):
                task_obj = Task.objects.filter(id=task_id).first()
                context['note'] = note
                context['task'] = task_obj
                context['file'] = obj
                context['DOMAIN'] = get_current_site(request)
                if task_obj.responsible_user:
                    SignalSystem.email(task_obj.responsible_user.email, _("A new file has been uploaded to a Task note"), 'email_note_file.html', context) # responsible user
            
                #SignalSystem.email(task_obj.from_user.email, _("A new file has been uploaded to a Task note"), 'email_note_file.html', context) # task tulajdonos

                """
                for user_obj in task_obj.to_user.all():
                    context['user_obj'] = user_obj
                    SignalSystem.email(user_obj.email, _("A new file has been uploaded to a Task note"), 'email_note_file.html', context)
                """

                return redirect('project:project_task_detail',  project_id, task_id)
            elif(meet_id):
                meet_obj = Meet.objects.filter(id=meet_id).first()
                context['note'] = note
                context['meet'] = meet_obj
                context['file'] = obj
                context['DOMAIN'] = get_current_site(request)
                for user_obj in meet_obj.to_user.all():
                    context['user_obj'] = user_obj
                    SignalSystem.email(user_obj.email, _("A new file has been uploaded to a Meet note"), 'email_note_file.html', context)
                
                return redirect('project:project_meet_detail',  project_id, meet_id)
            elif(form_id):
                return redirect('project:project_form_detail',  project_id, form_id)
            else:
                return redirect('project:project_note_index',  project_id)
    else:
        form = FileCreateForm()
    return render(request, 'note/upload.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


@login_required
def project_note_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    note = Note.objects.filter(id=id, project=project).first()
    if request.method == 'POST':
        #  megvizsgálom ha van e get paraméterbe
        task_id = request.GET.get('task_id')
        meet_id = request.GET.get('meet_id')
        form = NoteEditForm(request.POST, instance=note)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.save()

            try:
                # Activity create
                Activity.objects.create(project=project, user=user, name=_("Edit note"),
                                        description=f'{user.first_name} {user.last_name} _("edited the note:") {note.name} in {project.name}')
            except:
                # TODO: error handling
                pass

            messages.success(request, _('Succesfully saved!'))
            if (task_id):
                return redirect('project:project_task_detail', project_id, task_id)
            elif(meet_id):
                return redirect('project:project_meet_detail', project_id, meet_id)
            else:
                return redirect('project:project_note_index', project_id)
    else:
        form = NoteEditForm(instance=note)
    return render(request, 'note/edit.html', {'form': form, 'note': note, 'project': project})


@login_required
def project_note_task_create_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    task = Task.objects.filter(id=id, project=project).first()

    if task.archived == True:
        raise Http404

    if request.method == 'POST':
        form = NoteTaskCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.task = task
            obj.type = 'TASK'
            obj.save()
            form.save()

            try:
                # Activity create
                Activity.objects.create(project=project, user=user, name=_("New message"),
                                        description=f'{_("New message on")} {project.name} ({task.name}) {_("by")} {user.first_name} {user.last_name}')
            except:
                # TODO: error handling
                pass

            #Email send
            context['task'] = task
            context['note'] = obj
            context['DOMAIN'] = get_current_site(request)
            if task.responsible_user:
                SignalSystem.email(task.responsible_user.email, _("New note has been added to your task"), 'email_task_note.html', context)
            
            #SignalSystem.email(task.from_user.email, _("New note has been added to your task"), 'email_task_note.html', context)
            
            """
            for user_obj in task.to_user.all():
                context['user_obj'] = user_obj
                SignalSystem.email(user_obj.email, _("New note has been added to your task"), 'email_task_note.html', context)
            """

            return redirect('project:project_task_detail', project_id, id)
    else:
        form = NoteTaskCreateForm()
    return render(request, 'note/create_task_note.html', {'form': form, 'project': project, 'task': task, 'project_id': project_id, 'id': id})


@login_required
def project_task_archive_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    task = Task.objects.filter(id=id, project=project).first()
    Task.objects.filter(id=id, project=project).update(archived=True)

    try:
        # Activity
        Activity.objects.create(project=project, user=user, name=_("Archive task"),
                                description=f'{user.first_name} {user.last_name} {_("arhived task:")} {task.name} {_("in")} {project.name}')
    except:
        # TODO: error handling
        pass

    messages.success(request, _('Task archived'))
    return redirect('project:project_task_index', project_id)


@login_required
def project_task_unarchive_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    task = Task.objects.filter(id=id, project=project).first()
    Task.objects.filter(id=id, project=project).update(archived=False)

    try:
        # Activity
        Activity.objects.create(project=project, user=user, name=_("Unarchived task"),
                                description=f'{user.first_name} {user.last_name} {_("unarhived task:")} {task.name} {_("in")} {project.name}')
    except:
        # TODO: error handling
        pass

    messages.success(request, _('Task unarchived'))
    return redirect('project:project_task_index', project_id)

"""
MEET
"""


@login_required
def project_meet_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    x = permission_check(user, project)

    team = Team.objects.filter(user=user).first()

    if team.customer == True or team.staff == True:  # ezzel monodm meg, hogy ki mit láthat a fromok közül
        meets = Meet.objects.filter(project=project).exclude(lawyer_mode=True)
    else:
        meets = Meet.objects.filter(
            project=project, to_user=user).exclude(lawyer_mode=True)

    #meets = Meet.objects.filter(project = project).exclude(lawyer_mode = True)
    context = {}
    context['meets'] = meets
    context['project'] = project
    context['x'] = x
    return render(request, 'meet/index.html', context)



@login_required
# TODO: ezt átvinni a lawyeres részre is plsuz betöltetni a saját naptáramat ha van calnedar id.
def project_meet_create_view(request, project_id):
    user = request.user
    calendar_id = request.user.profile.calendar_id
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    if request.method == 'POST':
        form = MeetCreateForm(request.POST)
        if form.is_valid():
            # ----------
            name = form.cleaned_data.get('name')
            description = form.cleaned_data.get('description')
            to_users = form.cleaned_data.get('to_user')
            meet_start = form.cleaned_data.get('meet_start')
            meet_end = form.cleaned_data.get('meet_end')

            meet_start = str(meet_start)
            meet_end = str(meet_end)
            meet_start_raw = datetime.strptime(meet_start, '%Y-%m-%d %H:%M:%S+00:00')
            meet_end_raw = datetime.strptime(meet_end, '%Y-%m-%d %H:%M:%S+00:00')

            meet_start_raw = str(meet_start_raw).replace('+00:00', 'Z').replace(' ', 'T')
            meet_end_raw = str(meet_end_raw).replace('+00:00', 'Z').replace(' ', 'T')


            """
            INNEN KEZDŐDIK A MEGHIVÁSOS BUZISÁG CHEKKER
            """
            invite_email = form.cleaned_data.get('invite_email')

            if(invite_email != ''):
                team = Team.objects.filter(user__email=invite_email).filter(project=project_id).exclude(active=False).exists()
                user_in_system = User.objects.filter(email=invite_email).first()
                email_in_system = Invite.objects.filter(invite_email=invite_email).first() # megvizsgálja hogy van e mar emghivott személy --> ezt majd
                # TODO: törölni kell azacceptnél az a bzitos!


                if(invite_email == user.email):
                    messages.warning(request, _('The email addres dont your email'))
                    return redirect('project:project_meet_create', project_id, id)
                elif(team):
                    messages.warning(request, _('The email addres can find in dropdown list.'))
                    return redirect('project:project_meet_create', project_id, id)
              
            """
            VÉGE A CHEKKERNEK
            """

            # ----------
            obj = form.save(commit=False)
            obj.from_user = user
            obj.project = project
            obj.save()
            form.save_m2m()

            yz = []
            for y in to_users:
                yz.append(y.email)

            """
            MEGHIVÁSOS BUZISÁG LOGIKA EZT KELL MAJD COPYZNI A FORMHOZ MEG A DOKUMENTUMHOZ
            """
            #megnézem hogy lézetik e egyáltalán a cucc és h nem üres
            if(invite_email != ''):
                meet_obj = Meet.objects.filter(id = obj.id).first()
                # megnézem hogy a rendszerbe bennt van e az email. Ha igen akkor megy a meghivó, + hozzávonom a taskot is
                if(user_in_system):
                    #Ha igen akkor megy a meghivó, + hozzávonom a taskot hozzáadás
                    # megkeresm a meghivást ha már létezik akkor csak hozzáadom a személyt ha nem létezik akkro létrehozom
                    invite_in_system = Invite.objects.filter(recipient=user_in_system).first() 
                    
                    try:
                    
                        if(invite_in_system):
                            #csak hozzáadom a személyt 
                            Invite.objects.get(id=invite_in_system.id).meet.add(meet_obj)
                            Activity.objects.create(project=project, name=_('Assinged to meet - személy létezik a meghivások között csak hozzáadom'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                        else:
                            # Invite + task adding + team
                            team_obj, team_created = Team.objects.get_or_create(
                                email=user_in_system.email,
                                project=project,
                                user=user_in_system,
                                token=None
                            )
                            invite = Invite.objects.create(sender=request.user, sender_display_name='Legisly system', recipient=user_in_system,
                                                action=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}', description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}.', project=project)
                            Invite.objects.get(id=invite.id).meet.add(meet_obj)
                            #Activity
                            Activity.objects.create(project=project, name=_('Invite new people - létrehozom a személyt meet'), description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}')
                            Activity.objects.create(project=project, name=_('Assinged to meet - létrehozom a személyt és hozzá is adom'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                    except:
                        # TODO: error handling
                        pass

                #TODO: ha a temaben mar szerepel azt is meg kell lesni

                elif(email_in_system):
                    # email_in_system == magával az invite objectel
                    #megkeresem az adott meghívást és hozzácsapom a taskot
                    Invite.objects.get(id=email_in_system.id).meet.add(meet_obj)
                    Activity.objects.create(project=project, name=_('Assinged to meet - személy létezik a meghivások között még nem aktiv user...'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')

                else:
                    #tokent hozok létre számára
                    print('Egyáltalán nincs a rendszerben a User emailes meghívó')
                    # team_type=team_type_obj ezt majd betenni ha szűkség lesz rá
                    # kell előszőr egy useert generalni majd egy meghivast is é majd ezt kell feldolgozni 
                    # teambe kell létrehozni egy meghivást
                    # ha megvan a meghivás akkor valahogy hozzá kell baszatni azt is hogy a taskot is megkapja

                    token = uuid.uuid4()
                    # 1 Create a team user  
                    team_obj, team_created = Team.objects.get_or_create(
                        project=project,
                        token=str(token),
                        email = invite_email
                    )
                    # 2 Create invite
                    invite_obj = Invite.objects.create(
                        project=project,
                        recipient = None,
                        invite_email = invite_email,
                        sender=request.user, 
                        sender_display_name= f'{request.user.first_name} {request.user.last_name}',
                        description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on tokenes")} {project.name}'
                    )

                    Invite.objects.get(id=invite_obj.id).meet.add(meet_obj)

                    # Activity
                    Activity.objects.create(project=project, name=_('Invite new people - ismeretlen - meet - személy'),
                                            description=f'{_("The client sent invite email for")} ({invite_email}) {_("for this project:")} {project.name}.')

                    Activity.objects.create(project=project, name=_('Assinged to meet - ismeretlen - még nem is regisztrált'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                
                    # Email
                    context[''] = team_created
                    context['project'] = project
                    context['user_obj'] = user
                    invite_link = f'https://app.legisly.com/register/invite/{token}'
                    context['invite_link'] = invite_link
                    context['sender'] = request.user
                    context['DOMAIN'] = get_current_site(request)
                    SignalSystem.email('sikler.sikler@gmail.com', _("You have been invited to collaborate in a legal case - ismeretlen meet"), 'email_project_invite.html', context)

            """
            MEGHIVÁSOS  BUZISÁG LOGIKÁJÁNAK A VÉGE 
            """

            # Call function calendar.py ----------
            #calendar_create_view(calendar_id, name, description,to_users, meet_start, meet_end, obj.id)

            
            event = {
                'summary': str(name),
                'location': '',
                'description': str(description),
                'start': {
                    'dateTime': meet_start_raw,
                    'timeZone': 'Europe/Budapest',
                },
                'end': {
                    'dateTime': meet_end_raw,
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

                'attendees': 
                [
                    {'email': request.user.email },
                 
                ],

                'reminders': {
                    'useDefault': True,
                },

            }

            event_link = ''

            if request.user.profile.calendar_id:
                try:
                    SCOPES = ['https://www.googleapis.com/auth/calendar']
                    SERVICE_ACCOUNT_FILE = 'credentials.json'
                    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

                    delegated_credentials = credentials.with_subject('info@legisly.com')
                    service = build('calendar', 'v3', credentials=delegated_credentials)

                    #TODO: ide jöjjön be az ügyvéd id-ja ha nincs akkor el se inditsa ezt a szálat request.user.profile.calendar_id
                    event = service.events().insert(calendarId=request.user.profile.calendar_id,
                                                    conferenceDataVersion=1, body=event,).execute()
                    #print('Event created: %s' % (event.get('hangoutLink')))
                    event_link = event.get('hangoutLink')
                    event_id = event.get('id')
                except:
                    messages.warning(request, _('Error with API. Please restart the create action'))
                    Meet.objects.filter(id = obj.id).delete()
                    return redirect('project:project_meet_index', project_id)

            else:
                messages.warning(request, _('Error not valid calendar id. Please restart the create action'))
                Meet.objects.filter(id = obj.id).delete()
                return redirect('project:project_meet_index', project_id)
             
            try:
                # Add ME to meet
                
                Meet.objects.get(id=obj.id).to_user.add(user)
                Meet.objects.filter(id=obj.id).update(url = event_link, google_calendar_id = event_id)
                meet_obj = Meet.objects.filter(id=obj.id).first()
                
                # Activity 
                Activity.objects.create(project=project, name=_("Meet created"),
                                        description=f'{user.first_name} {user.last_name} {_("invited you to a consultation on")} {meet_start} {_("Case:")} {project.name}.')
            
                
                #Email send
                context['meet'] = meet_obj
                context['invite'] = request.user
                context['DOMAIN'] = get_current_site(request)
                for user_obj in meet_obj.to_user.all():
                    context['user_obj'] = user_obj
                    SignalSystem.email(user_obj.email, _("You have been invited to a consultation"), 'email_meet.html', context)


            except:
                # TODO: error handling
                pass

            
            # Notification create XY invited you to a consultation on <date>. Case: <project.name>
            for to_user in to_users:
                SignalSystem.notification(request.user, (request.user.first_name + ' ' + request.user.last_name), to_user, _(
                    f"{request.user.first_name} {request.user.last_name} {_('invited you to a consultation on')} {meet_start}. {_('Case:')} {project.name}."), 'INFO', '')

        

            messages.success(request, _('Sucessfully created'))
            return redirect('project:project_meet_index', project_id)
    else:
        form = MeetCreateForm()
        type_choices = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).exclude(
            user__profile__user_role=3).exclude(active=False).exclude(user=user).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['to_user'] = forms.MultipleChoiceField(
            choices=type_choices, label=_('User'), help_text=_('E-mail címet adjon meg'))

    return render(request, 'meet/create.html', {'form': form, 'project': project})


def project_meet_invite_view(request, project_id, id):
    user = request.user
    calendar_id = request.user.profile.calendar_id
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    meet = Meet.objects.filter(id = id).first()
    context = {}
    data = []
    # Check permission
    permission_check(user, project)
    if request.method == 'POST':
        form = MeetInviteForm(request.POST)
        if form.is_valid():
            to_users = form.cleaned_data.get('to_user')
        

            for to_user in to_users:
                if to_user in meet.to_user.all():
                    messages.warning(request, _('User already added to meet'))
                    return redirect('project:project_meet_index', project_id)
                else:
                    meet.to_user.add(to_user)
                    SignalSystem.notification(request.user, (request.user.first_name + ' ' + request.user.last_name), to_user, _(
                    f"{request.user.first_name} {request.user.last_name} {_('invited you to a consultation on')} {meet.meet_start}. {_('Case:')} {project.name}."), 'INFO', '')

                    context['meet'] = meet
                    context['user_obj'] = to_user
                    context['invite'] = request.user
                    context['DOMAIN'] = get_current_site(request)
                    SignalSystem.email(to_user.email, _("Invite meet"), 'email_meet.html', context)



                #item = {"email": user.email}
                #data.append(item)

            """
            try:
                SCOPES = ['https://www.googleapis.com/auth/calendar']
                SERVICE_ACCOUNT_FILE = 'credentials.json'
                credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

                delegated_credentials = credentials.with_subject('info@legisly.com')
                service = build('calendar', 'v3', credentials=delegated_credentials)

                #TODO: ide jöjjön be az ügyvéd id-ja ha nincs akkor el se inditsa ezt a szálat request.user.profile.calendar_id
                event = service.events().patch(eventId=meet.google_calendar_id ,calendarId='c_3gkjm7oka2lloj4le429lpr2ig@group.calendar.google.com', body=event,).execute()
                #print('Event created: %s' % (event.get('hangoutLink')))
                event_link = event.get('hangoutLink')
                event_id = event.get('id')
            except:
                pass
            """

            #notify
            """
            for to_user in to_users:
                SignalSystem.notification(user, (user.first_name + ' ' + user.last_name), to_user, _(
                    f"{user.first_name} {user.last_name} {_('invited you to a consultation on')} {meet.meet_start}. {_('Case:')} {project.name}."), 'INFO', '')

            #email
            
            for to_user in to_users:
                context['meet'] = meet
                context['user_obj'] = to_user
                context['invite'] = request.user
                SignalSystem.email(to_user.email, _("Invite meet"), 'email_meet.html', context)
            """

            messages.success(request, _('Sucessfully invited'))
            return redirect('project:project_meet_index', project_id)
    
    else:
        form = MeetInviteForm()
        type_choices = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).exclude(
                user__profile__user_role=3).exclude(active=False).exclude(user=user).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['to_user'] = forms.MultipleChoiceField(choices=type_choices, label=_('User'))

    return render(request, 'meet/invite.html', {'form': form, 'project': project})


def project_meet_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    meet = Meet.objects.filter(id = id).first()
    context = {}
  
    # Check permission
    permission_check(user, project)
    if request.method == 'POST':
        form = MeetEditForm(request.POST, instance=meet)
        if form.is_valid():
            form.save()

            messages.success(request, _('Sucessfully save'))
            return redirect('project:project_meet_index', project_id)
    
    else:
        form = MeetEditForm(instance=meet)
        type_choices = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).exclude(
                user__profile__user_role=3).exclude(active=False).exclude(user=user).values('user', 'user__first_name', 'user__last_name','user__email')]
  
        form.fields['to_user'] = forms.MultipleChoiceField(choices=type_choices, label=_('User'))

    return render(request, 'meet/edit.html', {'form': form, 'project': project})

@login_required
def project_meet_detail_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    x = permission_check(user, project)

    meet = Meet.objects.filter(id=id, project=project).first()
    notes = Note.objects.filter(project=project, meet=meet)
    context = {}
    context['meet'] = meet
    context['project'] = project
    context['notes'] = notes
    context['x'] = x
    return render(request, 'meet/detail.html', context)


@login_required
def project_meet_create_file_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    meet = Meet.objects.filter(id=id).first()
    if request.method == 'POST':
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.uploaded_by = user
            obj.project = project
            obj.meet = meet
            obj.file_type = 'MEET'
            obj.save()
            form.save()

            try:
                # Activity 
                Activity.objects.create(project=project, user=user, name=_("Upload new file to meet"),
                                        description=f'{user.first_name} {user.last_name} {_("uploaded a new file to")} {meet.name}')
            except:
                # TODO: error handling
                pass

            #Email send
            context['meet'] = meet
            context['file_obj'] = obj
            context['DOMAIN'] = get_current_site(request)
            for user_obj in meet.to_user.all():
                context['user_obj'] = user_obj
                SignalSystem.email(user_obj.email, _("A new file has been uploaded to your consultation"), 'email_meet_file.html', context)

            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_meet_detail', project_id, id)
    else:
        form = FileCreateForm()
    return render(request, 'meet/upload.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


@login_required
def project_note_meet_create_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    meet = Meet.objects.filter(id=id, project=project).first()
    if request.method == 'POST':
        form = NoteMeetCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.meet = meet
            obj.type = 'MEET'
            obj.save()
            form.save()

            try:
                # Activity 
                Activity.objects.create(project=project, name=_('Add new note'),
                                        description=f'{_("New message on")} {project.name} ({meet.name}) {_("by")} {user.first_name} {user.last_name}')
            except:
                # TODO: error handling
                pass

            context['note'] = obj
            context['meet'] = meet
            context['DOMAIN'] = get_current_site(request)
            for user_obj in meet.to_user.all():
                context['user_obj'] = user_obj
                SignalSystem.email(user_obj.email, _("Added a new note to your consultation"), 'email_meet_note.html', context)

            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_meet_detail', project_id, id)
    else:
        form = NoteMeetCreateForm()
    return render(request, 'note/create_meet_note.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


def project_meet_delete_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    meet_obj = Meet.objects.filter(id=id, project = project).first()

    try:
        # Activity 
        Activity.objects.create(project=project, name=_("Meet deleted"), description=f'{user.first_name} {user.last_name} {_("deleted the consultation")}. {_("Case:")} {project.name}.')
    except:
        pass

    
    for to_user in meet_obj.to_user.all():
        SignalSystem.notification(request.user, (request.user.first_name + ' ' + request.user.last_name), to_user, _(
            f"{request.user.first_name} {request.user.last_name} {_('deleted the consultation')}. {_('Case:')} {project.name}."), 'INFO', '')


    """
    for to_user in to_users:
        context['meet_start'] = meet_start
        context['project_name'] = project.name
        context['created_by'] = str(user.first_name + ' ' + user.last_name)
        context['meet_end'] = meet_end
        context['project_id'] = project.id
        SignalSystem.email(to_user.email,
                            _("Created meet"), 'email_meet.html', context)
    """

    #TODO: call Calendar API
    try:
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        SERVICE_ACCOUNT_FILE = 'credentials.json'
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        delegated_credentials = credentials.with_subject('info@legisly.com')
        service = build('calendar', 'v3', credentials=delegated_credentials)
        #TODO: majd az adott személyre kciserélni ezt.
        event = service.events().delete(calendarId=request.user.profile.calendar_id, eventId=meet_obj.google_calendar_id).execute()
        Meet.objects.filter(id=id, project=project).delete()
        messages.success(request, _('Deleted'))
    except:
        messages.success(request, _('Deleted, but google calendar check it(maybe problem with API)'))
        Meet.objects.filter(id=id, project=project).delete()


    return redirect('project:project_meet_index', project_id)

"""
TASK
"""


@login_required
def project_task_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    x = permission_check(user, project)

    team = Team.objects.filter(user=user).first()

    if team.customer == True or team.staff == True:  # ezzel monodm meg, hogy ki mit láthat a fromok közül
        tasks = Task.objects.filter(project=project).exclude(lawyer_mode=True)
    else:
        tasks = Task.objects.filter(
            project=project, to_user=user).exclude(lawyer_mode=True)

    #tasks = Task.objects.filter(project = project).exclude(lawyer_mode = True)
    context = {}
    context['tasks'] = tasks
    context['project'] = project
    context['x'] = x
    return render(request, 'task/index.html', context)

"""
class ClerkPermission(PermissionRequiredMixin)
    def has_permission(self):
        return self.super() and self.user.is_clerck

class RecordDetailView(View,LoginRequiredMixin,ClerkPermission):
   
    def get(self,request,args,kwargs):
        pass

    def post(self,request,args,kwargs):
        pass
"""

@login_required
def project_task_create_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    x =permission_check(user, project)

    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            #responsible_user = form.cleaned_data.get('responsible_user')
            
            """
            INNEN KEZDŐDIK A MEGHIVÁSOS BUZISÁG CHEKKER
            """
            invite_email = form.cleaned_data.get('invite_email')

            if(invite_email != ''):
                team = Team.objects.filter(user__email=invite_email).filter(project=project_id).exclude(active=False).exists()
                user_in_system = User.objects.filter(email=invite_email).first()

                email_in_system = Invite.objects.filter(invite_email=invite_email).first() # megvizsgálja hogy van e mar emghivott személy --> ezt majd
                # TODO: törölni kell azacceptnél az a bzitos!


                if(invite_email == user.email):
                    messages.warning(request, _('The email addres dont your email'))
                    return redirect('project:project_task_create', project_id)
                elif(team):
                    messages.warning(request, _('The email addres can find in dropdown list.'))
                    return redirect('project:project_task_create', project_id)
                
                """
                elif(email_in_system):
                    messages.warning(request, _('Proba'))
                    return redirect('project:project_task_create', project_id)
                """

            """
            VÉGE A CHEKKERNEK
            """

            obj = form.save(commit=False)
            obj.from_user = user
            obj.project = project
            obj.save()
            to_users = form.cleaned_data.get('to_user')
            form.save_m2m()

            """
            MEGHIVÁSOS BUZISÁG LOGIKA EZT KELL MAJD COPYZNI A FORMHOZ MEG A DOKUMENTUMHOZ
            """
            #megnézem hogy lézetik e egyáltalán a cucc és h nem üres
            if(invite_email != ''):
                task_obj = Task.objects.filter(id = obj.id).first()
                # megnézem hogy a rendszerbe bennt van e az email. Ha igen akkor megy a meghivó, + hozzávonom a taskot is
                if(user_in_system):
                    #Ha igen akkor megy a meghivó, + hozzávonom a taskot hozzáadás
                    # megkeresm a meghivást ha már létezik akkor csak hozzáadom a személyt ha nem létezik akkro létrehozom
                    invite_in_system = Invite.objects.filter(recipient=user_in_system).first() 
        
                    try:
                        if(invite_in_system):
                            #csak hozzáadom a személyt 
                            Invite.objects.get(id=invite_in_system.id).task.add(task_obj)
                            Activity.objects.create(project=project, name=_('Assinged to task - személy létezik a meghivások között csak hozzáadom'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                        else:
                            # Invite + task adding + team
                            team_obj, team_created = Team.objects.get_or_create(
                                email=user_in_system.email,
                                project=project,
                                user=user_in_system,
                                token=None
                            )
                            invite = Invite.objects.create(sender=request.user, sender_display_name='Legisly system', recipient=user_in_system,
                                                action=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}', description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}.', project=project)
                            Invite.objects.get(id=invite.id).task.add(task_obj)
                            #Activity
                            Activity.objects.create(project=project, name=_('Invite new people - létrehozom a személyt task'), description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}')
                            Activity.objects.create(project=project, name=_('Assinged to task - létrehozom a személyt és hozzá is adom'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                    except:
                        # TODO: error handling
                        pass

                #TODO: ha a temaben mar szerepel azt is meg kell lesni

                elif(email_in_system):
                    # email_in_system == magával az invite objectel
                    #megkeresem az adott meghívást és hozzácsapom a taskot
                    Invite.objects.get(id=email_in_system.id).task.add(task_obj)
                    Activity.objects.create(project=project, name=_('Assinged to task - személy létezik a meghivások között még nem aktiv user...'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')

                else:
                    #tokent hozok létre számára
                    #Egyáltalán nincs a rendszerben a User emailes meghívó')
                    token = uuid.uuid4()
                    # 1 Create a team user  
                    team_obj, team_created = Team.objects.get_or_create(
                        project=project,
                        token=str(token),
                        email = invite_email
                    )
                    # 2 Create invite
                    invite_obj = Invite.objects.create(
                        project=project,
                        recipient = None,
                        invite_email = invite_email,
                        sender=request.user, 
                        sender_display_name= f'{request.user.first_name} {request.user.last_name}',
                        description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on tokenes")} {project.name}'
                    )

                    Invite.objects.get(id=invite_obj.id).task.add(task_obj)

                    # Activity
                    Activity.objects.create(project=project, name=_('Invite new people - ismeretlen - task - személy'),
                                            description=f'{_("The client sent invite email for")} ({invite_email}) {_("for this project:")} {project.name}.')

                    Activity.objects.create(project=project, name=_('Assinged to task - ismeretlen - még nem is regisztrált'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                
                    # Email
                    context[''] = team_created
                    context['project'] = project
                    context['user_obj'] = user
                    invite_link = f'https://app.legisly.com/register/invite/{token}'
                    context['invite_link'] = invite_link
                    context['sender'] = request.user
                    context['DOMAIN'] = get_current_site(request)
                    SignalSystem.email('sikler.sikler@gmail.com', _("You have been invited to collaborate in a legal case - ismeretlen task"), 'email_project_invite.html', context)

            """
            MEGHIVÁSOS  BUZISÁG LOGIKÁJÁNAK A VÉGE 
            """
            try:
                task_obj = Task.objects.filter(id=obj.id).first()
                #1 Activity created for dropdown users
                Activity.objects.create(project=project, user=request.user, name=_("Added new task"),
                                        description=f'{_("You received a new task on")} {project.name} {_("by")} {user.first_name} {user.last_name} {_("Due date: ")} {task_obj.due_date}')
            except:
                pass

            #2 Notification create
            for to_user in to_users:
                SignalSystem.notification(request.user, (request.user.first_name + ' ' + request.user.last_name), to_user, f'{_("You received a new task on")} {project.name} {_("by")} {request.user.first_name} {request.user.last_name}', 'INFO', '')

            #3 Email send
            task_obj = Task.objects.filter(id=obj.id).first()
            context['task'] = task_obj
            context['DOMAIN'] = get_current_site(request)
            
            for user_obj in task_obj.to_user.all():
                context['user_obj'] = user_obj
                SignalSystem.email(user_obj.email, _("You have been assigned a new task"), 'email_task.html', context)

            try:
                #4 Add ME to task
                Task.objects.get(id=obj.id).to_user.add(user)
            except:
                pass

            messages.success(request, _('Successfully created'))
            return redirect('project:project_task_index', project_id)
    else:
        form = TaskCreateForm()
        #type_choices = [(i['user'], i['name']) for i in Team.objects.filter(project = project).filter(role = 2).exclude(user = None).exclude(user = request.user).values('user', 'name')]
        #form.fields['responsible_user'] = forms.ChoiceField(choices=type_choices,required=False)
        # TODO: majd itt be kell löni hogy teljes nevet írjon ki
        type_choices2 = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).exclude(
            user__profile__user_role__gt=2).exclude(user=None).exclude(user=user).exclude(active=False).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['to_user'] = forms.MultipleChoiceField(
            choices=type_choices2, label=_('User'), required=False)

        """ 
        type_choices = [(i['user'], i['user__last_name']) for i in Team.objects.filter(project=project).exclude(
            user__profile__user_role__gt=2).exclude(user=None).exclude(user=user).exclude(active=False).values('user', 'user__first_name', 'user__last_name')]
        form.fields['responsible_user'] = forms.ModelChoiceField(
            queryset=type_choices, label=_('Responsible user'))
        """
    return render(request, 'task/create.html', {'form': form,'x':x, 'project': project})


@login_required
def project_task_detail_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    x = permission_check(user, project)

    task = Task.objects.filter(id=id, project=project).first()
    if task.archived == True:
        raise Http404

    notes = Note.objects.filter(
        project=project, task=task).exclude(lawyer_mode=True)
    context = {}
    context['task'] = task
    context['notes'] = notes
    context['project'] = project
    context['x'] = x
    return render(request, 'task/detail.html', context)


@login_required
def project_task_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    task = Task.objects.filter(id=id, project=project).first()
    if task.archived == True:
        raise Http404

    if request.method == 'POST':
        form = TaskEditForm(request.POST, instance=task)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            form.save_m2m()

            try:
                # Activity create
                Activity.objects.create(project=project, user=request.user, name=_("Edited task"),
                                        description=f'{user.first_name} {user.last_name} {_("edited the task:")} {task.name} {_("in")} {project.name}')
            except:
                # TODO:
                pass
            messages.success(request, _('Successfully saved'))
            return redirect('project:project_task_index', project_id)
    else:
        form = TaskEditForm(instance=task)
        type_choices = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).filter(
            role=2).exclude(user=None).exclude(user=request.user).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['responsible_user'] = forms.ChoiceField(
            choices=type_choices, required=False, label=_('User'))

    return render(request, 'task/edit.html', {'form': form, 'project': project})

@login_required
def project_task_responsible_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)
    task = Task.objects.filter(id=id).first()
    if task.archived == True:
        raise Http404
    
    if request.method == 'POST':
        form = TaskResponsibleForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            responsible_user = form.cleaned_data['responsible_user']
            form.save()

            try:
                # Activity
                Activity.objects.create(project=project, user=user, name=_("Responsible user added"),
                                        description=f'{user.first_name} {user.last_name} {_("added responsible user to task:")} {task.name}')
            except:
                # TODO:
                pass
            
            SignalSystem.notification(request.user, (request.user.first_name + ' ' + request.user.last_name), responsible_user, _(f"{vuser.first_name} {request.user.last_name} {_('added responsible user to task:')} {task.name}. {_('Case:')} {project.name}."), 'INFO', '')


            #Email send

            context['task'] = task
            context['DOMAIN'] = get_current_site(request)
            user_obj = User.objects.filter(username= responsible_user).first()
            context['user_obj'] = user_obj
            SignalSystem.email(user_obj.email, _("You have been assigned a new task"), 'email_task_assignee.html', context)
            
         

            messages.success(request, _('Successfully'))
            return redirect('project:project_task_index', project_id)
    else:
        form = TaskResponsibleForm(instance=task)
        type_choices = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).filter(
            user__profile__user_role = 2).exclude(user=None).exclude(user=user).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['responsible_user'] = forms.ChoiceField(
            choices=type_choices, label=_('Responsible user'))
    return render(request, 'task/responsible.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


@login_required
def project_task_create_file_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    permission_check(user, project)

    task = Task.objects.filter(id=id).first()
    if task.archived == True:
        raise Http404

    if request.method == 'POST':
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            task_file = form.cleaned_data['project_file']
            obj = form.save(commit=False)
            obj.uploaded_by = user
            obj.project = project
            obj.task = task
            obj.file_type = 'TASK'
            obj.save()
            form.save()

            try:
                # Activity
                Activity.objects.create(project=project, user=user, name=_("Upload new file to task"),
                                        description=f'{user.first_name} {user.last_name} {_("uploaded a new file to")} {task.name}')
            except:
                # TODO:
                pass

            #Email send
            context['task'] = task
            context['file'] = obj
            context['DOMAIN'] = get_current_site(request)
            if task.responsible_user:
                SignalSystem.email(task.responsible_user.email, _("Uploaded a new file for the task"), 'email_task_file.html', context) # responsible user
            
            #SignalSystem.email(task.from_user.email, _("Uploaded a new file for the task"), 'email_task_file.html', context) # task tulajdonos
           
            """
            for user_obj in task.to_user.all():
                context['user_obj'] = user_obj
                SignalSystem.email(user_obj.email, _("Uploaded a new file for the task"), 'email_task_file.html', context)
            """


            messages.success(request, _('Successfully created'))
            return redirect('project:project_task_detail', project_id, id)
    else:
        form = FileCreateForm()
    return render(request, 'task/upload.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


"""
MESSAGE
"""


@login_required
def project_message_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    context = {}
    # Check permission
    x = permission_check(user, project)

    team_qs = Team.objects.filter(project = project, active = True).exclude(role='3')
    message_obj = Message.objects.filter(project=project).exclude(
        lawyer_mode=True).order_by('created_at')

    if request.method == 'POST':
        form = MessageCreateForm(request.POST)
        formUpload = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.save()

            for team_obj in team_qs:
                context['team_obj'] = team_obj
                context['message'] = obj
                context['DOMAIN'] = get_current_site(request)
                SignalSystem.email(team_obj.user.email, _("You have received new message(s) for your case"), 'email_message.html', context)

            return redirect('project:project_message_index', project_id)

        elif formUpload.is_valid():
            obj2 = formUpload.save(commit=False)
            obj2.uploaded_by = user
            obj2.project = project
            obj2.file_type = 'MESSAGE'
            obj2.save()
            formUpload.save()
            last_file = File.objects.filter(id=obj2.id).first()
            Message.objects.create(
                content=last_file.name, url=last_file.project_file.url, user=user, project=last_file.project)

            try:
                # Activity create
                Activity.objects.create(project=project, user=user, name=_("Upload new file"),
                                        description=f'{user.first_name} {user.last_name} {_("added new file in message")} - {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('Upload success'))
            return redirect('project:project_message_index', project_id)
    else:
        form = MessageCreateForm()
        formUpload = FileCreateForm()
    return render(request, 'message/index.html', {'form': form,'x':x , 'formUpload': formUpload, 'message_obj': message_obj, 'project': project})


@login_required
def project_message_users_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    teams = Team.objects.filter(project=project).exclude(
        role__gte=3)  # az admint és az officost kizárjuk

    context = {}
    context['project'] = project
    context['teams'] = teams
    return render(request, 'message/users.html', context)


@login_required
def project_message_files_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    files = File.objects.filter(project=project, file_type='MESSAGE')
    context = {}
    context['project'] = project
    context['files'] = files
    return render(request, 'message/files.html', context)


"""
FILE
"""


@login_required
def project_file_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    file_obj = File.objects.filter(project=project).exclude(lawyer_mode=True)
    context = {}
    context['file_obj'] = file_obj
    context['project'] = project
    return render(request, 'file/index.html', context)


@login_required
def project_file_detail_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    file_obj = File.objects.filter(id=id, project=project).first()
    if file_obj.archived == True:
        raise Http404
    context = {}
    context['file_obj'] = file_obj
    context['project'] = project
    return render(request, 'file/detail.html', context)


@login_required
def project_file_create_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    if request.method == 'POST':
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            #file = form.cleaned_data['profile_picture']
            obj = form.save(commit=False)
            obj.uploaded_by = request.user
            obj.project = project
            obj.save()
            form.save()
            return redirect('project:project_file_index', project_id)
    else:
        form = FileCreateForm()

    return render(request, 'file/create.html', {'form': form, 'project': project})


@login_required
def project_file_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    file_obj = File.objects.filter(id=id).first()
    if file_obj.archived == True:
        raise Http404

    if request.method == 'POST':
        form = FileEditForm(request.POST, instance=file_obj)
        task_id = request.GET.get('task_id')
        meet_id = request.GET.get('meet_id')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()

            try:
                # Activity
                Activity.objects.create(project=project, user=user, name=_("Edit file"),
                                        description=f'{user.first_name} {user.last_name} {_("edited file:")} {file_obj.name} {_("in")} {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('File saved'))
            if(task_id):
                return redirect('project:project_task_detail', project_id, task_id)
            elif(meet_id):
                return redirect('project:project_meet_detail', project_id, meet_id)
            else:
                return redirect('project:project_file_index', project_id)
    else:
        form = FileEditForm(instance=file_obj)

    return render(request, 'file/edit.html', {'form': form, 'file_obj': file_obj, 'project': project})


@login_required
def project_file_archive_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    file_obj = File.objects.filter(id=id, project=project).first()
    File.objects.filter(id=id, project=project).update(archived=True)

    if request.method == 'GET':
        task_id = request.GET.get('task_id')
        meet_id = request.GET.get('meet_id')
        note_id = request.GET.get('note_id')
        form_id = request.GET.get('form_id')
        msg_id = request.GET.get('msg_id')

        try:
            # Activity
            Activity.objects.create(project=project, user=user, name=_("Archive file"),
                                    description=f'{user.first_name} {user.last_name} {_("arhived file:")} {file_obj.name} {_("in")} {project.name}')
        except:
            # TODO:
            pass

        messages.success(request, 'File archived')
        if(task_id):
            return redirect('project:project_task_detail', project_id, task_id)
        elif(meet_id):
            return redirect('project:project_meet_detail', project_id, meet_id)
        elif(form_id):
            return redirect('project:project_form_detail', project_id, form_id)
        elif(note_id):
            return redirect('project:project_note_index', project_id)
        elif(msg_id):
            return redirect('project:project_message_files_view', project_id)
        else:
            return redirect('project:project_file_index', project_id)


@login_required
def project_file_unarchive_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    file_obj = File.objects.filter(id=id, project=project).first()
    File.objects.filter(id=id, project=project).update(archived=False)

    if request.method == 'GET':
        task_id = request.GET.get('task_id')
        meet_id = request.GET.get('meet_id')
        note_id = request.GET.get('note_id')
        form_id = request.GET.get('form_id')
        msg_id = request.GET.get('msg_id')

        try:
            # Activity
            Activity.objects.create(project=project, user=user, name=_("Unarchived file"),
                                    description=f'{user.first_name} {user.last_name} {_("unarhived file:")} {file_obj.name} {_("in")} {project.name}')
        except:
            # TODO:
            pass

        messages.success(request, 'File unarchived')
        if(task_id):
            return redirect('project:project_task_detail', project_id, task_id)
        elif(meet_id):
            return redirect('project:project_meet_detail', project_id, meet_id)
        elif(form_id):
            return redirect('project:project_form_detail', project_id, form_id)
        elif(note_id):
            return redirect('project:project_note_index', project_id)
        elif(msg_id):
            return redirect('project:project_message_files_view', project_id)
        else:
            return redirect('project:project_file_index', project_id)

@login_required
def project_file_delete_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    File.objects.filter(id=id).filter(project=project).delete()

    if request.method == 'GET':
        task_id = request.GET.get('task_id')
        meet_id = request.GET.get('meet_id')
        form_id = request.GET.get('form_id')
        messages.success(request, _('File deleted'))
        if(task_id):
            return redirect('project:project_task_detail', project_id, task_id)
        elif(meet_id):
            return redirect('project:project_meet_detail', project_id, meet_id)
        elif(form_id):
            return redirect('project:project_form_detail', project_id, form_id)
        else:
            return redirect('project:project_file_index', project_id)


"""
FORMS
"""


@login_required
def project_form_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    team = Team.objects.filter(user=user).first()

    # only can access from to user involed the form
    if team.customer == True or team.staff == True:  # ezzel monodm meg, hogy ki mit láthat a fromok közül
        form_qs = ProjectForm.objects.filter(
            project=project)  # TODO: majd filtetrezni
    else:
        form_qs = ProjectForm.objects.filter(
            project=project, to_user=user)  # TODO: majd filtetrezni

    context = {}
    context['form_qs'] = form_qs
    context['project'] = project
    # TODO: majd átirni sima indexre
    return render(request, 'form/index.html', context)


@login_required
def project_form_detail_view(request, project_id, id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    form_obj = ProjectForm.objects.filter(
        id=id).first()  # TODO: majd filtetrezni

    notes = Note.objects.filter(project=project, project_form=form_obj)
    context = {}
    context['form_obj'] = form_obj
    context['notes'] = notes
    context['project'] = project
    return render(request, 'form/detail.html', context)


@login_required
def project_form_create_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    #try get order number
    order_obj = Order.objects.filter(id = project.order_number).first()
    # Check permission
    permission_check(user, project)

    if request.method == 'POST':
        form = CreateForm(request.POST, request.FILES)
        if form.is_valid():
            multiple = form.cleaned_data.get('multiple') # megkapom a szorzot
            default_form = form.cleaned_data.get('default_form') #megkapom az id a forntendről
            form_obj = ProjectFormDefault.objects.filter(name = default_form).first() #objektumot megkapom
            # time paramter
            now = datetime.now()
            add_day = int(form_obj.start_date_plus_day)
            due_date = now + timedelta(days=add_day)
            # clone ciklus
            i = 1
            while i <= multiple:
                ProjectForm.objects.create(name = form_obj.name,button_text = form_obj.button_text, question= form_obj.question, project=project, start_date=now, due_date=due_date,form_schema=form_obj.default_schema, form_meta=form_obj.default_meta)
                i += 1

            """
            try:
                # Activity
                Activity.objects.create(project=project, user=user, name=_("Upload file to project form"),
                                        description=f'{user.first_name} {user.last_name} {_("upload new file for the form:")} {form_obj.name} {_("in")} {project.name}')
            except:
                # TODO: error handling
                pass
            """

            messages.success(request, _('Succesfully created!'))
            return redirect('project:project_form_index', project_id)
    else:
        # megnézem hogy létezik e még az order id révén a product, ha nem akkor hozza be simán a formot
        if order_obj:
            form = CreateForm(product_id=order_obj.product.id)
        else:
            form = CreateForm()

    return render(request, 'form/create.html', {'form': form, 'project': project, 'project_id': project_id})


@login_required
def project_form_duplicate_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    # Check permission
    permission_check(user, project)

    form_obj = ProjectForm.objects.filter(id = id).first()

    if request.method == 'POST':
        form = DuplicateForm(request.POST)
        if form.is_valid():
            multiple_number = form.cleaned_data.get('multiple_number') # megkapom a szorzot
            # clone ciklus
            if multiple_number != 1:
                i = 2
                while i <= multiple_number:
                    ProjectForm.objects.create(name = f'{form_obj.name} - clone {i}' ,button_text = form_obj.button_text, question= form_obj.question, project=project, start_date=form_obj.start_date, due_date=form_obj.due_date,form_schema=form_obj.form_schema,draft=True, form_meta=form_obj.form_meta, clone=True)
                    i += 1
            else:
                messages.warning(request, _('1 nél nafgyobbat adj meg'))
                return redirect('project:project_form_duplicate', project_id, id)

            ProjectForm.objects.filter(id = id).update(multiple=False, draft=False)

            messages.success(request, _('Succesfully duplicated!'))
            return redirect('project:project_form_index', project_id)
    else:
        # megnézem hogy létezik e még az order id révén a product, ha nem akkor hozza be simán a formot
        form = DuplicateForm()

    return render(request, 'form/duplicate.html', {'form': form, 'project': project,'form_obj':form_obj, 'project_id': project_id})


@login_required
def project_form_responsible_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    # Check permission
    permission_check(user, project)
    context = {}

    team = Team.objects.filter(project=project).exclude(user__profile__user_role=3).exclude(active=False).exclude(user=user)

    form_obj = ProjectForm.objects.filter(id = id).first()

    if request.method == 'POST':
        form = EditResponsibleForm(request.POST, instance=form_obj)
        if form.is_valid():
            responsible_user = form.cleaned_data.get('responsible_user')
            form.save()

            SignalSystem.notification(request.user, (request.user.first_name + ' ' + request.user.last_name), responsible_user, _(f"{request.user.first_name} {request.user.last_name} {_('added responsible user to form:')} {form_obj.name}. {_('Case:')} {project.name}."), 'INFO', '')


            #Email send
            context['form_obj'] = form_obj
            context['DOMAIN'] = get_current_site(request)
            context['from_user'] = user
            user_obj = User.objects.filter(username= responsible_user).first()
            context['user_obj'] = user_obj
            SignalSystem.email(user_obj.email , _("You have been assigned a new form"), 'email_form_assignee.html', context)
            
            try:
                # Activity
                Activity.objects.create(project=project, user=user, name=_("Added responsible user to form"),
                                        description=f'{user.first_name} {user.last_name} {_("added responsible user to form")} {form_obj.name} {_("in")} {project.name}')
            except:
                # TODO: error handling
                pass


            messages.success(request, _('Succesfully duplicated!'))
            return redirect('project:project_form_index', project_id)
    else:
        # megnézem hogy létezik e még az order id révén a product, ha nem akkor hozza be simán a formot
        form = EditResponsibleForm(instance=form_obj)
        type_choices = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).exclude(
            user__profile__user_role=3).exclude(active=False).exclude(user=user).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['responsible_user'] = forms.ModelChoiceField(
            queryset=type_choices, label=_('User'), help_text=_('E-mail címet adjon meg'))
        
    return render(request, 'form/responsible.html', {'form': form, 'project': project,'form_obj':form_obj, 'project_id': project_id})


@login_required
def project_form_edit_participant_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    # Check permission
    permission_check(user, project)
    context = {}
    form_obj = ProjectForm.objects.filter(id = id).first()

    if request.method == 'POST':
        form = EditParticipantForm(request.POST, instance=form_obj)
        if form.is_valid():
            
            """
            INNEN KEZDŐDIK A MEGHIVÁSOS BUZISÁG CHEKKER
            """
            invite_email = form.cleaned_data.get('invite_email')

            if(invite_email != ''):
                team = Team.objects.filter(user__email=invite_email).filter(project=project_id).exclude(active=False).exists()
                user_in_system = User.objects.filter(email=invite_email).first()

                email_in_system = Invite.objects.filter(invite_email=invite_email).first() # megvizsgálja hogy van e mar emghivott személy --> ezt majd
                # TODO: törölni kell azacceptnél az a bzitos!


                if(invite_email == user.email):
                    messages.warning(request, _('The email addres dont your email'))
                    return redirect('project:project_form_edit_participant', project_id, id)
                elif(team):
                    messages.warning(request, _('The email addres can find in dropdown list.'))
                    return redirect('project:project_form_edit_participant', project_id, id)
        
            """
            VÉGE A CHEKKERNEK
            """

            obj = form.save(commit=False)
            obj.save()
            form.save_m2m()

            """
            MEGHIVÁSOS BUZISÁG LOGIKA EZT KELL MAJD COPYZNI A FORMHOZ MEG A DOKUMENTUMHOZ
            """
            #megnézem hogy lézetik e egyáltalán a cucc és h nem üres
            if(invite_email != ''):
                last_form_obj = ProjectForm.objects.filter(id = obj.id).first()
                # megnézem hogy a rendszerbe bennt van e az email. Ha igen akkor megy a meghivó, + hozzávonom a taskot is
                if(user_in_system):
                    #Ha igen akkor megy a meghivó, + hozzávonom a taskot hozzáadás
                    # megkeresm a meghivást ha már létezik akkor csak hozzáadom a személyt ha nem létezik akkro létrehozom
                    invite_in_system = Invite.objects.filter(recipient=user_in_system).first() 
                    try:
                        if(invite_in_system):
                            #csak hozzáadom a személyt 
                            Invite.objects.get(id=invite_in_system.id).project_form.add(last_form_obj)
                            Activity.objects.create(project=project, name=_('Assinged to form - személy létezik a meghivások között csak hozzáadom'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                        else:
                            # Invite + task adding + team
                            team_obj, team_created = Team.objects.get_or_create(
                                email=user_in_system.email,
                                project=project,
                                user=user_in_system,
                                token=None
                            )
                            invite = Invite.objects.create(sender=request.user, sender_display_name='Legisly system', recipient=user_in_system,
                                                action=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}', description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}.', project=project)
                            Invite.objects.get(id=invite.id).project_form.add(last_form_obj)
                            #Activity
                            Activity.objects.create(project=project, name=_('Invite new people - létrehozom a személyt task'), description=f'{request.user.first_name} {request.user.last_name} {_("invited you to collaborate on")} {project.name}')
                            Activity.objects.create(project=project, name=_('Assinged to form - létrehozom a személyt és hozzá is adom'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                    except:
                        # TODO: error handling
                        pass

                #TODO: ha a temaben mar szerepel azt is meg kell lesni

                elif(email_in_system):
                    # email_in_system == magával az invite objectel
                    #megkeresem az adott meghívást és hozzácsapom a taskot
                    Invite.objects.get(id=email_in_system.id).project_form.add(last_form_obj)
                    Activity.objects.create(project=project, name=_('Assinged to form - személy létezik a meghivások között még nem aktiv user...'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')

                else:
                    #tokent hozok létre számára
                    print('Egyáltalán nincs a rendszerben a User emailes meghívó')
                  
                    token = uuid.uuid4()
                    # 1 Create a team user  
                    team_obj, team_created = Team.objects.get_or_create(
                        project=project,
                        token=str(token),
                        email = invite_email
                    )
                    # 2 Create invite
                    invite_obj = Invite.objects.create(
                        project=project,
                        recipient = None,
                        invite_email = invite_email,
                        sender=request.user, 
                        sender_display_name= f'{request.user.first_name} {request.user.last_name}',
                        description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on tokenes")} {project.name}'
                    )

                    Invite.objects.get(id=invite_obj.id).project_form.add(last_form_obj)

                    # Activity
                    Activity.objects.create(project=project, name=_('Invite new people - ismeretlen - task - személy'),
                                            description=f'{_("The client sent invite email for")} ({invite_email}) {_("for this project:")} {project.name}.')

                    Activity.objects.create(project=project, name=_('Assinged to task - ismeretlen - még nem is regisztrált'), description=f'{request.user.first_name} {request.user.last_name} {_("assinged you to a task on")} {project.name}')
                
                    # Email
                    context[''] = team_created
                    context['project'] = project
                    context['user_obj'] = user
                    invite_link = f'https://app.legisly.com/register/invite/{token}'
                    context['invite_link'] = invite_link
                    context['sender'] = request.user
                    context['DOMAIN'] = get_current_site(request)
                    SignalSystem.email('sikler.sikler@gmail.com', _("You have been invited to collaborate in a legal case - ismeretlen task"), 'email_project_invite.html', context)

            """
            MEGHIVÁSOS  BUZISÁG LOGIKÁJÁNAK A VÉGE 
            """
       
            try:
                # Activity
                Activity.objects.create(project=project, user=user, name=_("Added collaborators to form"),
                                        description=f'{user.first_name} {user.last_name} {_("Added collaborators to form")} {form_obj.name} {_("in")} {project.name}')
            except:
                # TODO: error handling
                pass
            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_form_index', project_id)
    else:
        # megnézem hogy létezik e még az order id révén a product, ha nem akkor hozza be simán a formot
        form = EditParticipantForm(instance=form_obj)

    return render(request, 'form/participant.html', {'form': form, 'project': project,'form_obj':form_obj, 'project_id': project_id})




@login_required
def project_form_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)
    # Check permission
    permission_check(user, project)

    form_obj = ProjectForm.objects.filter(id = id).first()

    if request.method == 'POST':
        form = EditForm(request.POST, instance=form_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_form_index', project_id)
    else:
        # megnézem hogy létezik e még az order id révén a product, ha nem akkor hozza be simán a formot
        form = EditForm(instance=form_obj)

    return render(request, 'form/edit.html', {'form': form, 'project': project,'form_obj':form_obj, 'project_id': project_id})



@login_required
def forms_index_view(request):
    test = ProjectForm.objects.first()

    return render(request, 'form/index.html', {'test': test})


@login_required
def project_form_create_file_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    form_obj = ProjectForm.objects.filter(id=id).first()
    if request.method == 'POST':
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.uploaded_by = user
            obj.project = project
            obj.project_form = form_obj
            obj.file_type = 'FORM'
            obj.save()
            form.save()

            try:
                # Activity
                Activity.objects.create(project=project, user=user, name=_("Upload file to project form"),
                                        description=f'{user.first_name} {user.last_name} {_("upload new file for the form:")} {form_obj.name} {_("in")} {project.name}')
            except:
                # TODO: error handling
                pass

            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_form_detail', project_id, id)
    else:
        form = FileCreateForm()
    return render(request, 'form/upload.html', {'form': form, 'form_obj': form_obj, 'project': project, 'project_id': project_id, 'id': id})


@login_required
def project_note_form_create_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    form_obj = ProjectForm.objects.filter(id=id, project=project).first()
    if request.method == 'POST':
        form = NoteFormCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.project_form = form_obj
            obj.type = 'FORM'
            obj.save()
            form.save()

            try:
                # Activity
                Activity.objects.create(project=project, name=_('Add note to project form'),
                                        description=f'{user.first_name} {user.last_name} {_("added new note the meet:")} {form_obj.name} {_("in")} {project.name}.')
            except:
                # TODO: error handling
                pass
            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_form_detail', project_id, id)
    else:
        form = NoteFormCreateForm()
    return render(request, 'note/create_form_note.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


"""
ACTIVITY
"""


@login_required
def project_activity_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False, closed = False)

    # Check permission
    permission_check(user, project)

    activities = Activity.objects.filter(
        project=project, lawyer_mode=False).order_by('-created_at')
    context = {}
    context['activities'] = activities
    context['project'] = project
    return render(request, 'activity/index.html', context)


@login_required
def project_lawyer_activity_index_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    activites = Activity.objects.filter(project=project, lawyer_mode=True)
    context = {}
    context['activites'] = activites
    context['project'] = project
    return render(request, 'lawyer/activity/index.html', context)


"""
-------------------------------------------------------------------------------------------------------
"""

"""
LAWYER - INDEX
"""


@login_required
@is_lawyer
def project_lawyer_index_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    activities = Activity.objects.filter(
        project=project, lawyer_mode=True).order_by('-created_at')[0:15]
    context = {}
    context['project'] = project
    context['activities'] = activities
    return render(request, 'lawyer/overview/index.html', context)


"""
LAWYER - NOTES
"""


@login_required
@is_lawyer
def project_lawyer_note_index_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    notes = Note.objects.filter(
        project=project, type='NOTE').filter(lawyer_mode=True)
    file_qs = File.objects.filter(Q(project=project, file_type='NOTE', lawyer_mode=True) and Q(
        project=project, file_type='DEFAULT', lawyer_mode=True))
    print(file_qs)
    context = {}
    context['notes'] = notes
    context['project'] = project
    context['file_qs'] = file_qs
    return render(request, 'lawyer/note/index.html', context)


@login_required
@is_lawyer
def project_lawyer_note_create_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    if request.method == 'POST':
        form = NoteCreateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.lawyer_mode = True
            obj.project = project
            obj.type = 'NOTE'
            obj.save()

            try:
                # Activity create
                Activity.objects.create(project=project, user=user, lawyer_mode=True, name=_("Created note"),
                                        description=f'{user.first_name} {user.last_name} {_("created new note: in")} {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('Succesfully saved!'))
            return redirect('project:project_lawyer_note_index', project_id)
    else:
        form = NoteCreateForm()
    return render(request, 'lawyer/note/create.html', {'form': form, 'project': project})


@login_required
@is_lawyer
def project_lawyer_note_create_file_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    note = Note.objects.filter(id=id).first()
    if request.method == 'POST':
        #  megvizsgálom ha van e get paraméterbe task note
        task_id = request.GET.get('task_id')
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.uploaded_by = request.user
            obj.project = project
            obj.lawyer_mode = True
            obj.note = note
            if(task_id):
                try:
                    obj.file_type = 'TASK_NOTE'
                    obj.task = Task.objects.get(id=task_id)
                except:
                    # TODO: error trigger berakni
                    obj.file_type = 'TASK_NOTE'
            else:
                try:
                    obj.file_type = 'NOTE'
                except:
                    # TODO: error trigger berakni
                    obj.file_type = 'NOTE'

            obj.save()
            form.save()
            messages.success(request, _('Succesfully saved!'))

            try:
                # Activity create
                Activity.objects.create(project=project, user=user, lawyer_mode=True, name=_("Upload file to note"),
                                        description=f'{user.first_name} {user.last_name} {_("upload new file in")} {project.name}')
            except:
                # TODO:
                pass

            if(task_id):
                return redirect('project:project_lawyer_task_detail',  project_id, task_id)
            else:
                return redirect('project:project_lawyer_note_index',  project_id)
    else:
        form = FileCreateForm()
    return render(request, 'lawyer/note/upload.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


@login_required
@is_lawyer
def project_lawyer_note_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)

    note = Note.objects.filter(id=id, project=project).first()
    if request.method == 'POST':
        #  megvizsgálom ha van e get paraméterbe
        task_id = request.GET.get('task_id')
        meet_id = request.GET.get('meet_id')
        form = NoteEditForm(request.POST, instance=note)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.save()

            try:
                # Activity create
                Activity.objects.create(project=project, user=user, name=_("Edit note"),
                                        description=f'{user.first_name} {user.last_name} {_("edited the note:")} {note.name} {_("in")} {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('Succesfully saved!'))
            if (task_id):
                return redirect('project:project_task_detail', project_id, task_id)
            elif(meet_id):
                return redirect('project:project_meet_detail', project_id, meet_id)
            else:
                return redirect('project:project_note_index', project_id)
    else:
        form = NoteEditForm(instance=note)
    return render(request, 'lawyer/note/edit.html', {'form': form, 'note': note, 'project': project})


"""
LAWYER - TASK
"""


@login_required
@is_lawyer
def project_lawyer_task_index_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    tasks = Task.objects.filter(project=project).exclude(lawyer_mode=False)
    context = {}
    context['tasks'] = tasks
    context['project'] = project
    return render(request, 'lawyer/task/index.html', context)


@login_required
@is_lawyer
def project_lawyer_task_archive_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    task = Task.objects.filter(id=id, project=project).first()
    Task.objects.filter(id=id, project=project).update(archived=True)

    try:
        # Activity
        Activity.objects.create(project=project, user=user, lawyer_mode=True, name=_("Archive task"),
                                description=f'{user.first_name} {user.last_name} {_("arhived task:")} {task.name} {_("in")} {project.name}')
    except:
        # TODO:
        pass
    messages.success(request, _('File archived'))
    return redirect('project:project_lawyer_task_index', project_id)



@login_required
@is_lawyer
def project_lawyer_task_detail_view(request, project_id, id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    task = Task.objects.filter(id=id, project=project).first()
    notes = Note.objects.filter(
        project=project, task=task).exclude(lawyer_mode=False)
    context = {}
    context['task'] = task
    context['notes'] = notes
    context['project'] = project
    return render(request, 'lawyer/task/detail.html', context)


@login_required
@is_lawyer
def project_lawyer_task_create_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            #responsible_user = form.cleaned_data.get('responsible_user')
            obj = form.save(commit=False)
            obj.from_user = user
            obj.project = project
            obj.lawyer_mode = True
            obj.save()
            form.save_m2m()

            try:
                # Add ME to task
                Task.objects.get(id=obj.id).to_user.add(user)
                # Activity create
                Activity.objects.create(project=project, user=request.user, lawyer_mode=True, name=_("Added new task"),
                                        description=f'{user.first_name} {user.last_name} {_("added new task in")} {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('Successfully created'))
            return redirect('project:project_lawyer_task_index', project_id)
    else:
        form = TaskCreateForm()

        type_choices2 = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).exclude(
            user__profile__user_role__gt=2).exclude(staff=False).exclude(user=None).exclude(user=user).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['to_user'] = forms.MultipleChoiceField(
            choices=type_choices2, label=_('User'))
    return render(request, 'lawyer/task/create.html', {'form': form, 'project': project})


@login_required
@is_lawyer
def project_lawyer_task_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    task = Task.objects.filter(id=id, project=project).first()
    if request.method == 'POST':
        form = TaskEditForm(request.POST, instance=task)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            form.save_m2m()

            try:
                # Activity create
                Activity.objects.create(project=project, lawyer_mode=True, user=request.user, name=_("Edited task"),
                                        description=f'{user.first_name} {user.last_name} {_("edited the task:")} {task.name} {_("in")} {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('Successfully saved'))
            return redirect('project:project_lawyer_task_index', project_id)
    else:
        form = TaskEditForm(instance=task)
        type_choices = [(i['user'], f"{i['user__email']} {i['user__last_name']} <{i['user__email']}>") for i in Team.objects.filter(project=project).filter(
            role=2).exclude(user=None).exclude(staff=False).exclude(user=request.user).values('user', 'user__first_name', 'user__last_name','user__email')]
        form.fields['responsible_user'] = forms.ChoiceField(
            choices=type_choices, required=False, label=_('User'))

    return render(request, 'lawyer/task/edit.html', {'form': form, 'project': project})


@login_required
@is_lawyer
def project_lawyer_task_create_file_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    task = Task.objects.filter(id=id).first()
    if request.method == 'POST':
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            task_file = form.cleaned_data['project_file']
            obj = form.save(commit=False)
            obj.uploaded_by = user
            obj.project = project
            obj.task = task
            obj.lawyer_mode = True
            obj.file_type = 'TASK'
            obj.save()
            form.save()

            try:
                # Activity
                Activity.objects.create(project=project, user=user, lawyer_mode=True, name=_("Upload file to task"),
                                        description=f'{user.first_name} {user.last_name} {_("upload new file for the task:")} {task.name} {_("in")} {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('Successfully created'))
            return redirect('project:project_lawyer_task_detail', project_id, id)
    else:
        form = FileCreateForm()
    return render(request, 'lawyer/task/upload.html', {'form': form, 'project': project, 'project_id': project_id, 'id': id})


@login_required
@is_lawyer
def project_lawyer_note_task_create_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    task = Task.objects.filter(id=id, project=project).first()
    if request.method == 'POST':
        form = NoteTaskCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.project = project
            obj.task = task
            obj.lawyer_mode = True
            obj.type = 'TASK'
            obj.save()
            form.save()

            try:
                # Activity create
                Activity.objects.create(project=project, user=user, lawyer_mode=True, name=_("Add note to task"),
                                        description=f'{user.first_name} {user.last_name} {_("added new note the task:")} {task.name} {_("in")} {project.name}')
            except:
                # TODO:
                pass

            return redirect('project:project_lawyer_task_detail', project_id, id)
    else:
        form = NoteTaskCreateForm()
    return render(request, 'lawyer/note/create_task_note.html', {'form': form, 'project': project, 'task': task, 'project_id': project_id, 'id': id})


"""
LAWYER - FILE
"""


@login_required
@is_lawyer
def project_lawyer_file_index_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    file_obj = File.objects.filter(project=project).exclude(lawyer_mode=False)
    context = {}
    context['file_obj'] = file_obj
    context['project'] = project
    return render(request, 'lawyer/file/index.html', context)


@login_required
@is_lawyer
def project_lawyer_file_detail_view(request, project_id, id):
    project = get_object_or_404(Project, id=project_id)
    file_obj = File.objects.filter(
        id=id, project=project).filter(lawyer_mode=True).first()
    context = {}
    context['file_obj'] = file_obj
    context['project'] = project
    return render(request, 'lawyer/file/detail.html', context)


@login_required
@is_lawyer
def project_lawyer_file_create_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    if request.method == 'POST':
        form = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            #file = form.cleaned_data['profile_picture']
            obj = form.save(commit=False)
            obj.uploaded_by = request.user
            obj.project = project
            obj.lawyer_mode = True
            obj.save()
            form.save()
            return redirect('project:project_lawyer_file_index', project_id)
    else:
        form = FileCreateForm()

    return render(request, 'lawyer/file/create.html', {'form': form, 'project': project})


@login_required
@is_lawyer
def project_lawyer_file_edit_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    file_obj = File.objects.filter(id=id).first()
    if request.method == 'POST':
        form = FileEditForm(request.POST, instance=file_obj)
        task_id = request.GET.get('task_id')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()

            try:
                # Activity
                Activity.objects.create(project=project, lawyer_mode=True, user=user, name=_("Edit file"),
                                        description=f'{user.first_name} {user.last_name} {_("edited file:")} {file_obj.name} {_("in")} {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('File saved'))
            if(task_id):
                return redirect('project:project_lawyer_task_detail', project_id, task_id)
            else:
                return redirect('project:project_lawyer_file_index', project_id)
    else:
        form = FileEditForm(instance=file_obj)

    return render(request, 'lawyer/file/edit.html', {'form': form, 'file_obj': file_obj, 'project': project})


@login_required
@is_lawyer
def project_lawyer_file_archive_view(request, project_id, id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    file_obj = File.objects.filter(id=id, project=project).first()
    File.objects.filter(id=id, project=project).update(archived=True)

    if request.method == 'GET':
        task_id = request.GET.get('task_id')
        note_id = request.GET.get('note_id')
        msg_id = request.GET.get('msg_id')

        try:
            # Activity
            Activity.objects.create(project=project, user=user, lawyer_mode=True, name=_("Archive file"),
                                    description=f'{user.first_name} {user.last_name} {_("arhived file:")} {file_obj.name} {_("in")} {project.name}')
        except:
            # TODO:
            pass

        messages.success(request, _('File archived'))
        if(task_id):
            return redirect('project:project_task_detail', project_id, task_id)
        elif(note_id):
            return redirect('project:project_lawyer_note_index', project_id)
        elif(msg_id):
            return redirect('project:project_message_files_view', project_id)
        else:
            return redirect('project:project_lawyer_file_index', project_id)


"""
LAWYER - MESSAGE
"""


@login_required
@is_lawyer
def project_lawyer_message_index_view(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, archived = False)
    message_obj = Message.objects.filter(project=project).exclude(
        lawyer_mode=False).order_by('created_at')

    if request.method == 'POST':
        form = MessageCreateForm(request.POST)
        formUpload = FileCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.lawyer_mode = True
            obj.project = project
            obj.save()
            return redirect('project:project_lawyer_message_index', project_id)

        elif formUpload.is_valid():
            obj2 = formUpload.save(commit=False)
            obj2.uploaded_by = user
            obj2.project = project
            obj2.file_type = 'MESSAGE'
            obj2.lawyer_mode = True
            obj2.save()
            formUpload.save()
            last_file = File.objects.filter(id=obj2.id).first()

            try:
                Message.objects.create(content=last_file.name, lawyer_mode=True,
                                       url=last_file.project_file.url, user=user, project=last_file.project)
                # Activity create
                Activity.objects.create(project=project, lawyer_mode=True, user=user, name=_("Upload new file"),
                                        description=f'{user.first_name} {user.last_name} {_("added new file in message")} - {project.name}')
            except:
                # TODO:
                pass

            messages.success(request, _('Upload success'))
            return redirect('project:project_lawyer_message_index', project_id)
    else:
        form = MessageCreateForm()
        formUpload = FileCreateForm()
    return render(request, 'lawyer/message/index.html', {'form': form, 'formUpload': formUpload, 'message_obj': message_obj, 'project': project})


@login_required
@is_lawyer
def project_lawyer_message_users_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    teams = Team.objects.filter(project=project).filter(staff=True)
    context = {}
    context['project'] = project
    context['teams'] = teams
    return render(request, 'lawyer/message/users.html', context)


@login_required
@is_lawyer
def project_lawyer_message_files_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, archived = False)
    files = File.objects.filter(
        project=project, file_type='MESSAGE').exclude(lawyer_mode=False)
    context = {}
    context['project'] = project
    context['files'] = files
    return render(request, 'lawyer/message/files.html', context)


"""
AJAX
"""


@login_required
def calendar_by_user(request):
    now = datetime.now(tz=timezone.utc)
    payload = {}
    if request.method == 'GET':
        user_id = request.GET.get("user_id")
        profile = Profile.objects.filter(user__id=user_id).first()
        calendar_id = profile.calendar_id  # get user calnedar id
        event = calendar_index_view(calendar_id)
        payload['user_id'] = user_id
        try:
            payload['response'] = 'TRUE'
            payload['event'] = event
            payload['user_id'] = user_id
        except:
            payload['response'] = 'FALSE'

    else:
        payload['response'] = "Error"
    return JsonResponse(payload)


@login_required
def project_next_meet_ajax(request):
    user = request.user

    now = datetime.now(tz=timezone.utc)
    # print(now)
    payload = {}
    if request.method == 'GET':
        project_id = request.GET.get("project_id")
        payload['project_id'] = project_id
        project = Project.objects.filter(id=project_id).first()
        try:
            meet = Meet.objects.filter(to_user=user,  project=project).filter(
                meet_start__gte=now).first()
            # print(meet)
            payload['response'] = 'TRUE'
            payload['url'] = meet.url
            payload['name'] = meet.name
            payload['meet_start'] = meet.meet_start #payload['date'] = meet.meet_start
            payload['meet_end'] = meet.meet_end #payload['time'] = meet.meet_end
        except:
            payload['response'] = 'FALSE'

    else:
        payload['response'] = "Error"
    return JsonResponse(payload)


import json
@login_required
def form_save_ajax(request):
    user = request.user

    payload = {}
    context = {}
    if request.method == 'GET':
        project_id = request.GET.get("project_id")
        values = request.GET.get("xxx")
        form_obj = request.GET.get("form_obj")

        val = json.loads(values) #concert to json
 
        try:
            project = Project.objects.filter(id=project_id).first()
            ProjectForm.objects.filter(project = project, id=form_obj).update(form_value=val)
            #SignalSystem.email('sikler.sikler@gmail.com', _("Your case is started!"), 'email_project_start.html', context)
            payload['response'] = 'TRUE'

            payload['xxx'] = val

        except:
            payload['response'] = 'FALSE'

    else:
        payload['response'] = "Error"
    return JsonResponse(payload)





def project_document_by_form(request):
    payload = {}
    context = {}
    if request.method == 'GET':
        form_id = request.GET.get("form_id")
        

        try:
            form_obj2 = ProjectForm.objects.filter(id=form_id).first()

            payload['response'] = 'TRUE'
            payload['form_obj2'] = form_obj2.form_value
        except:
            payload['response'] = 'FALSE'

    else:
        payload['response'] = "Error"
    return JsonResponse(payload)




def project_default_document_clone_view(request):
    payload = {}
    context = {}
    if request.method == 'GET':
        
        id_default_document = request.GET.get("id_default_document")
        try:
            
            document = DocumentDefault.objects.filter(id=id_default_document).first()

            payload['document'] = document.content
        except:
            payload['response'] = 'FALSE'

    else:
        payload['response'] = "Error"
    return JsonResponse(payload)