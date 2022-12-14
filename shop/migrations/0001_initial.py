# Generated by Django 3.2.10 on 2022-01-11 16:47

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('slug', models.SlugField(max_length=200, unique=True)),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=254)),
                ('slug', models.SlugField(max_length=254)),
                ('image', models.ImageField(blank=True, upload_to='')),
                ('short_description', models.TextField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('calendar', models.BooleanField(default=False)),
                ('video_url', models.CharField(blank=True, max_length=254, null=True)),
                ('start_time_hour', models.IntegerField(blank=True, default=1, null=True, validators=[django.core.validators.MaxValueValidator(24), django.core.validators.MinValueValidator(1)])),
                ('start_time_min', models.IntegerField(blank=True, default=1, null=True, validators=[django.core.validators.MaxValueValidator(59), django.core.validators.MinValueValidator(0)])),
                ('end_time_hour', models.IntegerField(blank=True, default=1, null=True, validators=[django.core.validators.MaxValueValidator(24), django.core.validators.MinValueValidator(1)])),
                ('end_time_min', models.IntegerField(blank=True, default=1, null=True, validators=[django.core.validators.MaxValueValidator(59), django.core.validators.MinValueValidator(0)])),
                ('duration', models.IntegerField(blank=True, default=1, null=True)),
                ('available', models.BooleanField(default=True)),
                ('label', models.CharField(blank=True, max_length=254, null=True)),
                ('type', models.CharField(choices=[('DEFAULT', 'Default'), ('COMPANY', 'Company'), ('APPOINTMENT', 'Appointment')], default='DEFAULT', max_length=254)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='shop.category')),
            ],
            options={
                'ordering': ('name',),
                'index_together': {('id', 'slug')},
            },
        ),
    ]
