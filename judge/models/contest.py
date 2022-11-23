from datetime import datetime, timezone

from django.db import models


class Contest(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

    def is_ongoing(self):
        time = datetime.now(tz=timezone.utc)
        return ((self.start_time is None or self.start_time <= time)
                and (self.end_time is None or time < self.end_time))

    def is_upcoming(self):
        time = datetime.now(tz=timezone.utc)
        return self.start_time is not None and time < self.start_time

    def is_past(self):
        time = datetime.now(tz=timezone.utc)
        return self.end_time is not None and self.end_time <= time
