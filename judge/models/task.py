from django.db import models

from judge.models.contest import Contest


class TaskData(models.Model):
    judge_code = models.CharField(max_length=30, unique=True)


class Task(models.Model):
    index = models.CharField(max_length=30)
    data = models.ForeignKey(TaskData, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    contest = models.ForeignKey(Contest, null=True, on_delete=models.CASCADE)
    statement_file = models.CharField(max_length=255)
    points = models.FloatField()
    time_limit = models.FloatField()
    memory_limit = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['contest', 'index'], name='unique_task_index'),
        ]
