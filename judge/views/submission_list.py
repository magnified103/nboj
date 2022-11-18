from judge.models import Submission
from judge.views.contest_base import ContestBaseView


class SubmissionListView(ContestBaseView):
    template_name = 'judge/contest_submission_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['submissions'] = Submission.objects.filter(user=self.user, task__contest=self.contest).order_by('-date')
        context['submission_status_processing'] = ['QU', 'P', 'G']
        context['submission_result_error'] = ['IE', 'SC', 'AB']

        return context
