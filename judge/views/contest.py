from django.views.generic import TemplateView

from judge.models import Participation, Task, User
from judge.utils.util import solved_task, get_best_score
from judge.views.contest_base import ContestMixin


class ContestView(ContestMixin, TemplateView):
    template_name = 'judge/contest_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['tasks'] = Task.objects.filter(contest=self.contest).order_by('index')
        context['tasks'] = Task.objects.raw('SELECT * FROM judge_task WHERE contest_id = %s '
                                            'ORDER BY judge_task.index ASC', [self.contest.id])
        user_ids = Participation.objects.filter(contest=self.contest).values_list('user_id', flat=True)
        for task in context['tasks']:
            # task.my_points = Submission.objects.filter(
            #     user=self.user, task=task).aggregate(Max('points', default=0))['points__max']
            task.my_points = get_best_score(self.user, task)
            task.no_of_solves = 0
            for user_id in user_ids:
                task.no_of_solves += solved_task(User.objects.get(id=user_id), task)
        return context
