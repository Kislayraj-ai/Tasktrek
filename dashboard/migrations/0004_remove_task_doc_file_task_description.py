# Generated by Django 4.1.13 on 2025-07-09 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_task_priority'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='doc_file',
        ),
        migrations.AddField(
            model_name='task',
            name='description',
            field=models.TextField(default='N/A', null=True),
        ),
    ]
