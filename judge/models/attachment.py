from django.db import models

from judge.models.contest import Contest
from judge.models.task import Task
from judge.models.user import User


class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_statement_file = models.BooleanField(default=False)
    path = models.URLField()
    fontawesome_icon_class = models.CharField(max_length=255, default='fa-solid fa-file')

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['task', 'name'], name='unique_attachment_name'),
        ]
