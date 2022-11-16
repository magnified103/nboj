from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView

from judge.models import Contest, Participation, Submission


class SubmissionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Contest
    template_name = 'judge/submission_list.html'

    def test_func(self):
        try:
            contest = Contest.objects.get(id=self.kwargs['contest_id'])
            user = self.request.user
            return Participation.objects.filter(contest=contest, user=user).count() > 0
        except Contest.DoesNotExist:
            return False

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        context['submission_list'] = Submission.objects.filter(
            user=self.request.user,
            task__contest_id=self.kwargs['contest_id']
        )
        return context
