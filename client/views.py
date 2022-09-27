from django.shortcuts import get_object_or_404, redirect, render
from client.models import Client
from django.http.response import HttpResponse, HttpResponseRedirect
from client.forms import ClientCreateForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _


@login_required
def client_index_view(request):
    context = {}
    clients = Client.objects.filter(user=request.user).exclude(archived=True)
    context['clients'] = clients
    return render(request, 'client/my_client.html', context)


@login_required
def client_detail_view(request, id):
    context = {}
    client = get_object_or_404(Client, id=id, user=request.user)
    context['client'] = client
    return render(request, 'client/detail.html', context)


@login_required
def client_create_view(request):
    if request.method == 'POST':
        product_id = request.GET.get('product_id')
        start_date = request.GET.get('start_date')
        date_time = request.GET.get('date_time')

        form = ClientCreateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, _('Client created'))

            if start_date and date_time and product_id:
                return HttpResponseRedirect(f'/order/create/{product_id}?start_date={start_date}&date_time={date_time}&product_id={product_id}')   
            elif product_id:
                return redirect('order:order_create', product_id=product_id)
            else:
                return redirect('client:client_index')
    else:
        form = ClientCreateForm()
    return render(request, 'client/create.html', {'form': form})


@login_required
def client_edit_view(request, id):
    user = request.user
    client = get_object_or_404(Client, id=id, user=user)  # 2x biztonság
    if request.method == 'POST':
        product_id = request.GET.get('product_id')
        form = ClientCreateForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            if product_id:
                return redirect('order:order_create', product_id=product_id)
            else:
                return redirect('client:client_index')
    else:
        form = ClientCreateForm(instance=client)
    return render(request, 'client/edit.html', {'form': form})


def client_archive_view(request, id):
    user = request.user
    # client = Client.objects.filter(id = id, user = user).update(archived = True)  #Mátét megkrédezni TODO
    Client.objects.filter(id=id, user=user).update(archived=True)
    messages.success(request, _('Archived'))
    return redirect('client:client_index')


@login_required
# itt bele kell egyezni az adminnak...
def client_delete_view(request, id):
    # adminnka üzi küldés hogy törlési igény történik
    # soft delete...
    user = request.user
    # client = Client.objects.filter(id = id, user = user).update(archived = True)  #Mátét megkrédezni TODO
    Client.objects.filter(id=id, user=user).delete()
    messages.success(request, _('Kliens siekresen törölve'))
    return redirect('client:client_index')
