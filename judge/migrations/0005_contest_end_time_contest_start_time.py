# Generated by Django 4.1.3 on 2022-11-11 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0004_remove_task_attachments'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='end_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='contest',
            name='start_time',
            field=models.DateTimeField(null=True),
        ),
    ]