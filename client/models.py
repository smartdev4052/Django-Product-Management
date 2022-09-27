from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

"""
COUNTRY - STATE - CITY
"""


class Country(models.Model):
    name = models.CharField(max_length=50)
    country_code = models.CharField(max_length=3, null=True, blank=True)

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    state_code = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name


CLIENT_TYPE = (
    ('PERSON', _('Person')),
    ('COMPANY', _('Company')),
)
"""
CLIENT MODEL
"""


class Client(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name='user_client')
    name = models.CharField(max_length=254)
    email = models.EmailField(max_length=120, null=True)
    type = models.CharField(
        max_length=20, choices=CLIENT_TYPE, default='PERSON')
    # Személyes adatok / képviseletre jogosult
    last_name = models.CharField(max_length=254, null=True, blank=True)
    first_name = models.CharField(max_length=254, null=True, blank=True)
    mother_name = models.CharField(max_length=254, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    house_number = models.CharField(max_length=10, null=True, blank=True)
    # Számlázás Székhely
    billing_country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, related_name='billing_country')
    billing_state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, related_name='billing_state')
    billing_city = models.ForeignKey(
        City, on_delete=models.SET_NULL, null=True, related_name='billing_city')
    billing_house_number = models.CharField(
        max_length=10, null=True, blank=True)
    tax_number = models.CharField(max_length=50, null=True, blank=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)
