# Generated by Django 3.2.10 on 2022-01-28 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0014_remove_documentdefault_form_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='invite',
            name='document',
            field=models.ManyToManyField(blank=True, to='project.Document'),
        ),
        migrations.AddField(
            model_name='invite',
            name='project_form',
            field=models.ManyToManyField(blank=True, to='project.ProjectForm'),
        ),
        migrations.AddField(
            model_name='invite',
            name='task',
            field=models.ManyToManyField(blank=True, to='project.Task'),
        ),
    ]
