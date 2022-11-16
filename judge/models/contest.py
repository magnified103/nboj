from django.db import models


class Contest(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
