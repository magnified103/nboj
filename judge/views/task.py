from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from judge.models import Participation, Task


class TaskView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'test_judge/contest_task.html'

    def test_func(self):
        try:
            contest = Task.objects.get(id=self.kwargs['task_id']).contest
            user = self.request.user
            return Participation.objects.filter(contest=contest, user=user).count() > 0
        except Task.DoesNotExist:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            task = Task.objects.get(id=self.kwargs['task_id'])
            context['task'] = task
            context['contest'] = task.contest
        except Task.DoesNotExist:
            raise PermissionDenied()
        return context
