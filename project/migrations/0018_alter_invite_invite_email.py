# Generated by Django 3.2.10 on 2022-01-28 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0017_invite_invite_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invite',
            name='invite_email',
            field=models.CharField(blank=True, max_length=254, null=True),
        ),
    ]
