from django import forms
from .models import Order
from shop.models import Product
from crispy_forms.helper import FormHelper


class OrderCreateForm(forms.ModelForm):
    date_start = forms.CharField(widget=forms.HiddenInput(), required=False)
    time_start = forms.CharField(widget=forms.HiddenInput(), required=False)
    duration = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Order
        fields = ['client', 'payment_method', 'date_start', 'time_start', 'duration', 'comment']
        exclude = ['quantity', 'paid', 'price', 'active', 'product']
       


class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['paid']
        exclude = ['client', 'quantity', 'price', 'product', 'active']
