from collections import Counter
import datetime as dt
from datetime import datetime, timedelta, time
from django import forms
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from notification.models import Notification
from order.forms import OrderCreateForm, OrderEditForm
from client.forms import ClientCreateForm
from order.models import Order
from project.models import Activity, Project, ProjectForm, ProjectFormDefault, Task, TaskDefault, Team
from shop.models import Product
from client.models import Client
from django.contrib.auth.models import User
from django.contrib import messages
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from smtplib import SMTPException
from django.template.loader import render_to_string
from core.utils import SignalSystem
from django.contrib.sites.shortcuts import get_current_site #domaint innen szerzem meg
from datetime import datetime, timedelta
from django.utils.translation import ugettext_lazy as _


@login_required
def order_index_view(request):
    context = {}
    user = request.user
    if user.profile.user_role == 1 or user.profile.user_role == 2:
        orders = Order.objects.filter(client__user=user)
        context = {}
        context['orders'] = orders
        return render(request, 'order/my_order.html', context)
    if user.profile.user_role == 3:
        orders = Order.objects.all().order_by('-id')
        context['orders'] = orders
        return render(request, 'order/index.html', context)


@login_required
def order_create_view(request, product_id):
    user = request.user
    now = datetime.now()
    product = Product.objects.filter(id=product_id).first()
    context = {}
    # speciális számozáshoz a kóód
    raw_today = datetime.today()
    str_today = str(raw_today.strftime("%y-%m-%d"))
    today = str_today.replace('-', '')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data.get('payment_method')  #payment_method
            client_id = form.cleaned_data.get('client')
            raw_start_date = form.cleaned_data.get(
                'date_start')  # get only date i.e. 2010-10-10
            duration = form.cleaned_data.get('duration')
            raw_start_time = form.cleaned_data.get(
                'time_start')  # get only time i.e. 10:10

            client = Client.objects.filter(name=client_id).first()

            # start_date + start_time
            if product.calendar == True:
                date_start_str = str(raw_start_date + ' ' + raw_start_time)
                date_start = datetime.strptime(
                    date_start_str, '%Y-%m-%d %H:%M')

                if date_start:
                    date__end = date_start + timedelta(minutes=int(duration))
                    date_end = date__end.strftime('%Y-%m-%d %H:%M')
            else:
                date_start = None #datetime.now()
                date_end = None #datetime.now()

            obj = form.save(commit=False)
            obj.user = user
            # megnézem hogy adott termék calnedaros e. Fontos ez mert ez alapján könnyne tudok szűrni mikor officos hozza létre az időpontot
            if product.calendar == True:
                obj.calendar = True
            else:
                obj.calendar = False
            obj.price = product.price

            obj.date_start = date_start  # ha van meet ip
            if date_start:
                obj.date_end = date_end  # ha van meet ip
            
            obj.price = product.price
            obj.product = product
            obj.name = product
            obj.customer = client
            obj.save()

            # Variable for create project
            order_id = obj.id
            order = Order.objects.filter(id=order_id).first()
            # speckós azonostióó
            project_name = f'{product.name} - ({today}-{order_id}-1)'

            # Automate create project
            project = Project.objects.create(
                name=project_name, description='', client=client, order_number=order_id)
            if(project):
                print('A project létrejött')
                Order.objects.filter(id=order_id).update(project=project)
            else:
                print('A project nem jött létre')

            # Add Officer to team
            create_office = Team.objects.create(
                email='info@legisly.com', project=project, role=3, staff=True, active=True, is_removable=False)
            if create_office:
                print('létrehozva')
            else:
                print('Nem lett hozzáadva az admin')

            # Add Client to team
            create_client = Team.objects.create(
                email=client.user.email, role=2, customer=True, user=client.user, project=project, active=True, is_removable=False)
            if create_client:
                Order.objects.filter(id=order_id).update(active=True)
                print('létrehozva')
            else:
                print('Nem lett hozzáadva a client')

            # Form search and create
            default_form = ProjectFormDefault.objects.filter(
                product=product, default_form=True)  #--> ez akkor jön képbe ha alapértelmezetten bnet vna a pipa
            for default in default_form:
                obj = ProjectFormDefault.objects.get(id=default.id)
                add_day = int(obj.start_date_plus_day)
                due_date = now + timedelta(days=add_day)
                ProjectForm.objects.create(name=f'#{order_id} - {obj.name} form - {project.name}',
                                           form_schema=obj.default_schema, form_meta=obj.default_meta, project=project, responsible_user=user, start_date=now,multiple=obj.multiple,question=obj.question,button_text = obj.button_text,due_date=due_date)
                # majd itt kell hozzáadni hogy many to many hozzáadja a team typot

            # Default task to project
            default_task = TaskDefault.objects.filter(product=product)
            for default in default_task:
                obj = TaskDefault.objects.get(id=default.id)
                add_day = int(obj.start_date_plus_day)
                due_date = now + timedelta(days=add_day)
                t = Task.objects.create(
                    name=f'{obj.name} - default', description=obj.description, project=project, start_date=now, due_date=due_date, responsible_user=user, from_user=user)
                t.to_user.add(user)

            try:
                # Activity
                Activity.objects.create(project=project, name=_('Project is created'),
                                        description=f'{_("The project is created. The project name:")} {project.name}.')
                Activity.objects.create(project=project, name=_('Team created'),
                                        description=f'{_("The client added to")} {project.name}.')
            except:
                # TODO: error
                pass

            # send email with task and others
            task_qs = Task.objects.filter(project = project)
            form_qs = ProjectForm.objects.filter(project = project)
            context['DOMAIN'] = get_current_site(request)
            context['client'] = client
            context['project'] = project
            context['task_qs'] = task_qs
            context['form_qs'] = form_qs
            context['user_obj'] = user
            context['product'] = product
            context['order'] = order
            #user.email
            SignalSystem.email(user.email, _("Your case is started!"), 'email_project_start.html', context)

            # payment_method email
            if payment_method == 'TRANSFER':
                SignalSystem.email(user.email, _("Thank you for your order!"), 'email_order_bank_transfer.html', context)
            elif payment_method == 'CARD':
                SignalSystem.email(user.email, _("Thank you for your order!"), 'email_order_card.html', context)
  
            messages.success(request, _('Order created!'))
            if user.profile.user_role == 1:
                return redirect('project:project_index')
            else:
                return redirect('order:order_index')
    else:
        form = OrderCreateForm()
        form.fields['client'] = forms.ModelChoiceField(
            Client.objects.filter(user=user).exclude(archived=True), label=_('Choose client'))
        

    return render(request, 'order/create.html', {'form': form, 'product': product, 'product_id': product_id})


@login_required
def order_detail_view(request, id):
    order = Order.objects.filter(id=id).first()
    context = {}
    context['order'] = order
    return render(request, 'order/detail.html', context)


def order_edit_view(request, id):
    order = Order.objects.filter(id=id).first()

    if request.method == 'POST':
        form = OrderEditForm(request.POST, instance=order)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, _('Saved'))

            return redirect('order:order_index')
        else:
            print('Hibás')
    else:
        form = OrderEditForm(instance=order)
    return render(request, 'order/edit.html', {'form': form, 'order': order})

# Csak admin


def order_delete_view(request, id):
    user = request.user
    order = Order.objects.filter(id=id).first()
    # Notify
    Notification.objects.create_notification(
        user, order.client.user, order.client.user, 'Megrendelés törlése', 'INFO', f'A megrendelés törölve - {order.client}')
    order.delete()
    messages.success(request, _('Kliens siekresen törölve'))
    return redirect('order:order_index')


def time_slots(start_time, end_time, duration):
    t = start_time
    while t <= end_time:
        yield t.strftime('%H:%M')
        t = (datetime.combine(datetime.today(), t) +
             timedelta(minutes=duration)).time()


# AJAX
@login_required
def order_ajax_client_view(request):
    user = request.user
    payload = {}
    if request.method == "GET":
        client_id = request.GET.get("client_id")

        client = Client.objects.filter(id=client_id, user=user).first()
        country = client.country.name
        billing_country = client.billing_country.name
        state = client.state.name
        billing_state = client.billing_state.name
        city = client.city.name
        billing_city = client.billing_city.name

        data = model_to_dict(client)
        # print(client)
        if(client):
            payload['response'] = "True"
            payload['client'] = data
            payload['country'] = country
            payload['billing_country'] = billing_country
            payload['state'] = state
            payload['billing_state'] = billing_state
            payload['city'] = city
            payload['billing_city'] = billing_city
        else:
            payload['response'] = "False"

    return JsonResponse(payload)


def json_slot(request):
    payload = {}
    if request.method == "GET":
        # rendes dátum pl. 2019-10-10
        calendly_date = request.GET.get("calendly_date")
        product_id = request.GET.get("product_id")

        product = Product.objects.filter(id=product_id).first()

        start_time_hour = product.start_time_hour  # from product
        start_time_min = product.start_time_min  # from product
        end_time_hour = product.end_time_hour  # from product
        end_time_min = product.end_time_min  # from product
        duration = product.duration  # from product

        date_from = datetime.strptime(calendly_date, '%Y-%m-%d')
        date_to = date_from + timedelta(days=1)

        # TODO: ide kell hogy csak az aktivakat kérdezze le, amiből lett is időpont azaz projekt
        foglalt = Order.objects.filter(
            date_start__range=(date_from, date_to))  # .exclude()

        print(foglalt)

        # emberek összeszámolása
        # emberek_szama =

        my_input = []
        for y in foglalt:
            # print(y.date_start)
            time = y.date_start.time()
            time = time.strftime("%H:%M")
            my_input.append(str(time))

        p = Counter(my_input)  # összeszámolom hogy miből mennyi van

        my_list = []  # egy ujabb végleges listába teszem csak egy bizonyos IF ággal megnézem a kapacitás számot
        for v in p:
            if(p[v] > 1):  # itt majd az a szám kell ahány ember van ezen a szakterületen 2 es az változó
                my_list.append(v)
            else:
                pass

        print(my_list)

        start_time = dt.time(start_time_hour, start_time_min)
        end_time = dt.time(end_time_hour, end_time_min)
        slots = list(time_slots(start_time, end_time, duration))

        # közös slotok kivonása
        res = list(set(slots) ^ set(my_list))
        # rendezés idő szerint
        res.sort(key=lambda date: datetime.strptime(date, "%H:%M"))
        # print(res)

        payload['response'] = "True"
        payload['slots'] = res
        payload['duration'] = duration

    return JsonResponse(payload)






#--------------------------
from django.views.decorators.clickjacking import xframe_options_exempt
def order_widget_view(request, product_id):
    user = request.user
    now = datetime.now()
    product = Product.objects.filter(id=product_id, calendar=True).first()
    if not product:
        return HttpResponse(_('Invalid product. Please try another product ID'))
    # speciális számozáshoz a kóód
    raw_today = datetime.today()
    str_today = str(raw_today.strftime("%y-%m-%d"))
    today = str_today.replace('-', '')

    return render(request, 'order/widget.html', {'product': product, 'product_id': product_id})
