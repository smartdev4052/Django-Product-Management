# Generated by Django 3.2.10 on 2022-01-13 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0008_projectform_draft'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectform',
            name='button_text',
            field=models.CharField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='projectform',
            name='question',
            field=models.CharField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='projectformdefault',
            name='button_text',
            field=models.CharField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='projectformdefault',
            name='question',
            field=models.CharField(blank=True, max_length=254, null=True),
        ),
    ]
