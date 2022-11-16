# Generated by Django 4.1.3 on 2022-11-11 10:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0002_remove_task_code_task_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='attachments',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='task',
            name='contest',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='judge.contest'),
        ),
        migrations.AlterField(
            model_name='task',
            name='statement_file',
            field=models.CharField(max_length=255),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('path', models.URLField()),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='judge.task')),
            ],
        ),
    ]