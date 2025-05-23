# Generated by Django 4.2.11 on 2025-05-21 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_alter_project_start_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectmember',
            name='role',
            field=models.CharField(choices=[('owner', 'Owner'), ('admin', 'Admin'), ('manager', 'Manager'), ('member', 'Member'), ('viewer', 'Viewer')], default='member', max_length=20),
        ),
    ]
