from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _

PRODUCT_TYPE = (
    ('DEFAULT', _('Default')),
    ('COMPANY', _('Company')),
    ('APPOINTMENT', _('Appointment')),
)


class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Currency(models.Model):
    name = models.CharField(max_length=254, null=True,)
    symbol = models.CharField(max_length=254, null=True,)
    
    def __str__(self):
        return self.symbol


class Tax(models.Model):
    name = models.CharField(max_length=254)
    rate = models.PositiveIntegerField()
    
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=254)
    slug = models.SlugField(max_length=254)
    image = models.ImageField(blank=True)
    short_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    calendar = models.BooleanField(default=False)
    video_url = models.CharField(max_length=254, null=True, blank=True)
    start_time_hour = models.IntegerField(default=1, null=True, blank=True, validators=[
                                          MaxValueValidator(24), MinValueValidator(1)])
    start_time_min = models.IntegerField(default=1, null=True, blank=True, validators=[
                                         MaxValueValidator(59), MinValueValidator(0)])
    end_time_hour = models.IntegerField(default=1, null=True, blank=True, validators=[
                                        MaxValueValidator(24), MinValueValidator(1)])
    end_time_min = models.IntegerField(default=1, null=True, blank=True, validators=[
                                       MaxValueValidator(59), MinValueValidator(0)])
    duration = models.IntegerField(default=1, null=True, blank=True)
    available = models.BooleanField(default=True)
    label = models.CharField(max_length=254, blank=True, null=True)
    tax = models.ForeignKey(Tax, related_name='tax_product', blank=True, null=True, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, related_name='currency_product', blank=True, null=True, on_delete=models.CASCADE)
    comment = models.BooleanField(default=False)
    # Ez mutatja meg majd hogy egyszerű projektről van szó vagy cégalapitás -- sablonizálásnál fontos
    type = models.CharField(choices=PRODUCT_TYPE,
                            max_length=254, default='DEFAULT')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        index_together = (('id', 'slug'),)

    def __str__(self):
        return self.name

    def brutto_price(self):
        if self.tax:
            return round(self.price * (1 + (self.tax.rate / 100)))
        else:
            return int(self.price)
