# Generated by Django 3.2.10 on 2022-02-02 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_auto_20220202_0831'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='symbol',
            field=models.CharField(max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='name',
            field=models.CharField(max_length=254, null=True),
        ),
    ]