from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from account.forms import ProfileEditForm, RegisterForm, LoginForm
from django.template.loader import render_to_string
from django.core.mail import send_mail
from smtplib import SMTPException
from core.utils import SignalSystem
from project.models import Team, Invite, Task, ProjectForm, Meet
from account.models import Profile
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site #domaint innen szerzem meg
from django.urls import reverse #új
 

def email_template(request):
    return render(request, 'email/email_note.html')


def email_test(request):
    context = {}
    context['username'] = 'proba'
    """
    SignalSystem.email('sikler.sikler@gmail.com', 'ez egy teszt class',
                       '', context)
    return HttpResponse('Email elküldve')

    """
    context = {}
    msg_html = render_to_string('email/email_project_start.html', context)
    
    send_mail('Üdvözöl a legisly.com', '', 'Legisly <info@legisly.com>',
                ['sikler.sikler@gmail.com'], fail_silently=True, html_message=msg_html,)
    
    return HttpResponse('Email elküldve')



"""
ACCOUNT
"""


def account_index_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    context = {}
    context['profile'] = profile
    return render(request, 'account/index.html', context)


def account_edit_view(request):
    user = request.user

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, _('Saved'))
            return redirect('account:account_index')

    else:
        form = ProfileEditForm(instance=user)
    return render(request, 'account/edit.html', {'form': form})


"""
VIEW - USER CREATE
"""
# Login


def login_page(request):
    form = LoginForm()
    message = ''
    if request.method == 'GET':
        product_id = request.GET.get('product_id')
        start_date = request.GET.get('start_date')
        date_time = request.GET.get('date_time')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        

        #From iframe
        start_date = request.GET.get('start_date')
        date_time = request.GET.get('date_time')
        product_id = request.GET.get('product_id')

        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                #messages.success(request, 'Legisly.com')
                
                if start_date and date_time and product_id:
                    return HttpResponseRedirect(f'/order/create/{product_id}?start_date={start_date}&date_time={date_time}&product_id={product_id}')
                elif product_id:
                    # megrendeléshez irányit tovább ott eldönthetem mit szeretnék
                    return redirect('order:order_create', product_id)
                else:
                    return redirect('project:project_index')

                    # return redirect('client:client_index') #összes kliense irányit
            else:
                message = 'Invalid login!'
    return render(
        request, 'register/login.html', context={'form': form, 'message': message})

# Register


def Register(request):
    if request.method == 'GET':
        product_id = request.GET.get('product_id')
        start_date = request.GET.get('start_date')
        date_time = request.GET.get('date_time')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        #From iframe
        start_date = request.GET.get('start_date')
        date_time = request.GET.get('date_time')
        product_id = request.GET.get('product_id')
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            password = form.cleaned_data.get('password')
            User.objects.create_user(
                username=username, email=email, password=password, first_name=first_name, last_name=last_name)
            user = authenticate(username=username, password=password)
            login(request, user)
            context = {}
            context['username'] = username
            context['first_name'] = first_name
            context['last_name'] = last_name
            context['DOMAIN'] = get_current_site(request)
            msg_html = render_to_string(
                'email/email_register_success.html', context)

            try:
                send_mail(_('Welcome to legisly.com'), '', 'Legisly <info@legisly.com>',
                          [email], fail_silently=True, html_message=msg_html,)
            except SMTPException as e:
                print('valami hiba....')

            messages.success(request, _('Welcome to Legisly'))

            if start_date and date_time and product_id:
                return HttpResponseRedirect(f'/order/create/{product_id}?start_date={start_date}&date_time={date_time}&product_id={product_id}')
               
            elif product_id:
                # átirányit hogy hozzak létre majd a termékhez KLIENS
                return redirect('order:order_create', product_id)
            else:
                # szimplán átirányit a kliensekre
                return redirect('client:client_index')
    else:
        form = RegisterForm()

    context = {'form': form}

    return render(request, 'register/register.html', context)


# Register
def RegisterInvite(request, token):

    team = Team.objects.filter(token=token).first()
    if(team is None):
        print('létezik')
        # TODO: vlaamit cisnéni kell
        return HttpResponse('Error! The tok is invalid')
    else:
        # Elindul a foylamat
        if request.method == 'POST':
            form = RegisterForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')
                password = form.cleaned_data.get('password')
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')

                # Mégegyszer lecsekkoljuk a emailt és a tokent
                check = Team.objects.filter(
                    token=token).filter(email=email).first()
                if(check):
                    print('Létezi ka user mehet a létrehozás....')
                    User.objects.create_user(
                        username=username, email=email, password=password, first_name=first_name, last_name=last_name)
                    user = authenticate(username=username, password=password)
                    login(request, user)
                    context = {}
                    context['first_name'] = first_name
                    context['last_name'] = last_name
                    context['username'] = username
                    context['DOMAIN'] = get_current_site(request)
                    
                    
                    
                    invited_user = Invite.objects.filter(project=check.project, invite_email = email).first()
   
                    for task in invited_user.task.all():
                        Task.objects.get(id=task.id).to_user.add(request.user)

                    for form in invited_user.project_form.all():
                        ProjectForm.objects.get(id=form.id).to_user.add(request.user)

                    for meet in invited_user.meet.all():
                        Meet.objects.get(id=meet.id).to_user.add(request.user)

                    Team.objects.filter(token=token).filter(
                        email=email).update(token=None, user=user, active=True)

                    msg_html = render_to_string(
                        'email/email_register_success.html', context)

                    try:
                        send_mail(_('Welcome to legisly.com'), '', 'Legisly <info@legisly.com>', [email], fail_silently=True, html_message=msg_html,)
                    except SMTPException as e:
                        print('valami hiba....')

                    messages.success(request, 'Welcome to legisly!')
                    # TODO: hobva irányitsuk majd a kliens hez vagy magéhoz az ügyhöz?
                    return redirect('project:project_index')
                else:
                    print('Nem létezik a user proba ujra')
                    messages.warning(request, _('Error email or token'))
                    form = RegisterForm()
                    context = {'form': form}
                    return render(request, 'register/register.html', context)
        else:
            form = RegisterForm()

        context = {'form': form}
        return render(request, 'register/register.html', context)
