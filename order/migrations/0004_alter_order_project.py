# Generated by Django 3.2.10 on 2022-01-14 14:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0010_project_responsible_user'),
        ('order', '0003_alter_order_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='project',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_project', to='project.project'),
        ),
    ]
