# Generated by Django 4.1.3 on 2022-11-17 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0007_submission_internal_result_alter_submission_memory_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='task',
            constraint=models.UniqueConstraint(fields=('contest', 'index'), name='unique_task_index'),
        ),
    ]
