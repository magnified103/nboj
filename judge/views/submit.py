from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import FormView

from judge.forms import EditorForm
from judge.judgeapi import judge_submission
from judge.models import Contest, Language, Participation, Task
from judge.views.contest_base import ContestMixin


class SubmitView(ContestMixin, FormView):
    template_name = 'judge/contest_submit.html'
    # template_name = 'judge/submit.html'
    form_class = EditorForm

    def get_success_url(self):
        return reverse('submissions', args=[self.contest.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'contest_id' in self.kwargs:
            kwargs['queryset'] = Task.objects.filter(contest=self.contest)
            if 'task' in self.request.GET:
                kwargs['initial'] = Task.objects.get(contest=self.contest, index=self.request.GET['task'])
        else:
            task_id = self.kwargs['task_id']
            kwargs['initial'] = Task.objects.get(contest=self.contest, id=task_id)
            kwargs['queryset'] = Task.objects.filter(contest=self.contest, id=task_id)

        return kwargs

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        submission = form.save(commit=False)
        submission.user = self.request.user
        submission.save()
        judge_submission(submission)
        return super().form_valid(form)
