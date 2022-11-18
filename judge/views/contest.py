from django.db.models import Max

from judge.models import Participation, Submission, Task
from judge.utils.util import solved_task
from judge.views.contest_base import ContestBaseView


class ContestView(ContestBaseView):
    template_name = 'judge/contest_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.objects.filter(contest=self.contest).order_by('index')
        users = Participation.objects.filter(contest=self.contest).values_list('user_id', flat=True)
        for task in context['tasks']:
            task.my_points = Submission.objects.filter(
                user=self.user, task=task).aggregate(Max('points', default=0))['points__max']
            task.no_of_solves = 0
            for user in users:
                task.no_of_solves += solved_task(user, task)
        return context
