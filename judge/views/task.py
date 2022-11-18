from django.utils.functional import cached_property

from django.utils.functional import cached_property

from judge.models import Task
from judge.views.contest_base import ContestBaseView


class TaskView(ContestBaseView):
    template_name = 'judge/contest_task.html'

    @cached_property
    def task(self):
        if 'task_id' in self.kwargs:
            return Task.objects.get(id=self.kwargs['task_id'])
        if 'contest_id' in self.kwargs and 'task_index' in self.kwargs:
            return Task.objects.get(index=self.kwargs['task_index'], contest_id=self.kwargs['contest_id'])
        raise Task.DoesNotExist()

    def test_func(self):
        if not super().test_func():
            return False
        try:
            _ = self.task
            return True
        except Exception:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = self.task
        return context
