from django.db import models

from judge.models.contest import Contest
from judge.models.user import User


class Participation(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['contest', 'user'], name='unique_participant'),
        ]
