import itertools
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.functional import cached_property
from django.views.generic import ListView

from judge.models import Contest, Participation, Task
from judge.utils.util import solved_task

logger = logging.getLogger('judge.views.dashboard')


class DashboardView(LoginRequiredMixin, ListView):
    model = Contest
    template_name = 'judge/dashboard.html'

    @cached_property
    def user(self):
        return self.request.user

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        contest_ids = Participation.objects.filter(user=self.request.user).values_list('contest_id', flat=True)
        # contest_ids = list(itertools.chain(*list(Participation.objects.raw('SELECT contest_id FROM judge_participation'
        #                                                                    'WHERE user_id = %s', [self.request.user.id]))))

        ongoing = []
        upcoming = []
        past = []

        for id in contest_ids:
            try:
                contest = Contest.objects.get(id=id)
                if contest.is_ongoing():
                    ongoing.append(contest)
                elif contest.is_upcoming():
                    upcoming.append(contest)
                else:
                    past.append(contest)
                tasks = Task.objects.filter(contest=contest)
                contest.tasks_solved = 0
                if contest.start_time is None or contest.end_time is None:
                    contest.duration = ''
                else:
                    contest.duration = int((contest.end_time - contest.start_time).total_seconds() * 1e3)
                for task in tasks:
                    if solved_task(self.user, task):
                        contest.tasks_solved += 1
            except Contest.DoesNotExist:
                logger.error(f'Contest with id={id} doesn\'t exist')

        context['ongoing'] = ongoing
        context['upcoming'] = upcoming
        context['past'] = past
        return context
