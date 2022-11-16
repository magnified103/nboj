from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.views.generic import TemplateView

from judge.models import Contest, Participation, Submission, Task


class ContestView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'test_judge/contest_overview.html'

    def test_func(self):
        try:
            contest = Contest.objects.get(id=self.kwargs['contest_id'])
            user = self.request.user
            return Participation.objects.filter(contest=contest, user=user).count() > 0
        except Contest.DoesNotExist:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            contest = Contest.objects.get(id=self.kwargs['contest_id'])
            context['tasks'] = Task.objects.filter(contest=contest)
            context['contest'] = contest

            for task in context['tasks']:
                task.my_points = Submission.objects.filter(
                    user=self.request.user, task=task).aggregate(Max('points'))['points__max']
        except Contest.DoesNotExist:
            raise PermissionDenied()
        return context
