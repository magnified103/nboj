from django.db import models

from judge.models.contest import Contest
from judge.models.language import Language


class TaskData(models.Model):
    judge_code = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.judge_code


class Task(models.Model):
    index = models.CharField(max_length=30)
    data = models.ForeignKey(TaskData, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    contest = models.ForeignKey(Contest, null=True, on_delete=models.CASCADE)
    points = models.FloatField()
    time_limit = models.FloatField()
    memory_limit = models.PositiveIntegerField()
    allowed_languages = models.ManyToManyField(Language)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['contest', 'index'], name='unique_task_index'),
        ]
