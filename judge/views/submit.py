from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import FormView

from judge.forms import EditorForm
from judge.judgeapi import judge_submission
from judge.models import Contest, Language, Participation, Task


class SubmitView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'test_judge/contest_submit.html'
    # template_name = 'judge/submit.html'
    form_class = EditorForm

    def test_func(self):
        try:
            if 'contest_id' in self.kwargs:
                contest = Contest.objects.get(id=self.kwargs['contest_id'])
            elif 'task_id' in self.kwargs:
                contest = Task.objects.get(id=self.kwargs['task_id']).contest
            else:
                return False
            user = self.request.user
            return Participation.objects.filter(contest=contest, user=user).count() > 0
        except Exception:
            return False

    def get_success_url(self):
        return reverse('contests')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            if 'contest_id' in self.kwargs:
                kwargs['contest'] = Contest.objects.get(id=self.kwargs['contest_id'])
            elif 'task_id' in self.kwargs:
                kwargs['selected_task'] = task = Task.objects.get(id=self.kwargs['task_id'])
                kwargs['contest'] = task.contest
            else:
                raise PermissionDenied()
        except Exception:
            raise PermissionDenied()
        return kwargs

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        submission = form.save(commit=False)
        submission.user = self.request.user
        submission.save()
        judge_submission(submission)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            if 'contest_id' in self.kwargs:
                context['contest'] = Contest.objects.get(id=self.kwargs['contest_id'])
            elif 'task_id' in self.kwargs:
                context['contest'] = Task.objects.get(id=self.kwargs['task_id']).contest
            else:
                raise PermissionDenied()
        except Exception:
            raise PermissionDenied()
        return context
