from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from judge.models import Contest, Participation


class ContestListView(LoginRequiredMixin, ListView):
    model = Contest
    template_name = 'judge/contest_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        contest_ids = Participation.objects.filter(user=self.request.user).values('contest_id')

        context['contest_list'] = Contest.objects.filter(id__in=contest_ids)
        return context
