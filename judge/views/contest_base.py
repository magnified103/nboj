from datetime import datetime, timezone

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import connection
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from judge.models import Contest, Participation, Task


class ContestMixin(LoginRequiredMixin, UserPassesTestMixin):

    @cached_property
    def contest(self):
        if 'contest_id' in self.kwargs:
            return Contest.objects.get(id=self.kwargs['contest_id'])
        if 'task_id' in self.kwargs:
            return Task.objects.get(id=self.kwargs['task_id']).contest
        raise Contest.DoesNotExist()

    @cached_property
    def user(self):
        return self.request.user

    def test_func(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM judge_participation '
                               'WHERE (contest_id = %s AND user_id = %s)', [self.contest.id, self.user.id])
                return cursor.fetchone()[0] > 0

            # return Participation.objects.filter(contest=self.contest, user=self.user).count() > 0
        except Exception:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contest'] = self.contest
        context['current_time'] = int(datetime.now(timezone.utc).timestamp() * 1e3)
        context['start_time'] = None if self.contest.start_time is None else int(self.contest.start_time.replace(tzinfo=timezone.utc).timestamp() * 1e3)
        context['end_time'] = None if self.contest.end_time is None else int(self.contest.end_time.replace(tzinfo=timezone.utc).timestamp() * 1e3)
        return context
