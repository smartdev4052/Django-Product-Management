from django.db import models
from shop.models import Product
from client.models import Client
from project.models import Project
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

PAYMENT_METHOD = (
    ('TRANSFER', _('Bank transfer')),
    ('CARD', _('Card')),
)

STATUS = (
    ('PENDING', _('Pending')),
    ('IN_PROGRESS', _('In progress')),
    ('CLOSED', _('Closed')),
    ('ARCHIVED', _('Archived')),
)



class Order(models.Model):
    client = models.ForeignKey(
        Client, related_name='order_client', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_product',
                                on_delete=models.SET_NULL, null=True, blank=True, default=None)
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name='order_project')
    customer = models.CharField(max_length=254, null=True, blank=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    comment = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)
    calendar = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    status = models.CharField(choices=STATUS,max_length=50, default='PENDING')
    lawyer = models.ManyToManyField(
        User, blank=True)  # hozzávonom a rendeléshez
    payment_method = models.CharField(choices=PAYMENT_METHOD,max_length=50, default='TRANSFER')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('id','-created_at')

    def __str__(self):
        return 'Order {}'.format(self.id)
