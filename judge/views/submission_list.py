from django.views.generic import TemplateView

from django import forms

from judge.forms import SubmissionFilterForm
from judge.models import Submission, Task, Language
from judge.views.contest_base import ContestMixin


class SubmissionListView(ContestMixin, TemplateView):
    template_name = 'judge/contest_submission_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # context['submissions'] = Submission.objects.filter(user=self.user, task__contest=self.contest).order_by('-date')
        query = Submission.objects.filter(user=self.user, task__contest=self.contest)
        # query = Submission.objects.raw('SELECT * FROM judge_submission INNER JOIN judge_task ON '
        #                                                '(judge_submission.task_id = judge_task.id) WHERE '
        #                                                '(judge_task.contest_id = %s AND judge_submission.user_id = %s) '
        #                                                'ORDER BY judge_submission.date DESC',
        #                                                [self.contest.id, self.user.id])
        initial_task = None
        if 'task' in self.request.GET:
            index = self.request.GET['task']
            initial_task = (index, Task.objects.get(contest=self.contest, index=index).name)
            query = query.filter(task__index=index)
        initial_language = None
        if 'language' in self.request.GET:
            key = self.request.GET['language']
            initial_language = (key, Language.objects.get(key=key).name)
            query = query.filter(language__key=key)
        initial_status = None
        if 'status' in self.request.GET:
            status = self.request.GET['status']
            initial_status = (status, status)
            query = query.filter(result=status)
        if 'order' in self.request.GET:
            order = self.request.GET['order']
            ok = True
            if order == 'BY_DATE_ASC':
                query = query.order_by('date')
            elif order == 'BY_DATE_DESC':
                query = query.order_by('-date')
            elif order == 'BY_POINT_ASC':
                query = query.order_by('points')
            elif order == 'BY_POINT_DESC':
                query = query.order_by('-points')
            elif order == 'BY_TIME_ASC':
                query = query.order_by('time')
            elif order == 'BY_TIME_DESC':
                query = query.order_by('-time')
            elif order == 'BY_MEMORY_ASC':
                query = query.order_by('memory')
            elif order == 'BY_MEMORY_DESC':
                query = query.order_by('-memory')
            else:
                # Default behavior
                query = query.order_by('-date')
                ok = False
            if ok:
                context['order'] = order
            else:
                context['order'] = ''
        else:
            # Default behavior
            query = query.order_by('-date')
            context['order'] = ''

        context['filter_form'] = SubmissionFilterForm(self.user, self.contest,
                                                      initial_task=initial_task,
                                                      initial_language=initial_language,
                                                      initial_status=initial_status
                                                      )
        context['submissions'] = query
        # context['submission_tasks'] = Submission.objects.filter(
        #     user=self.user,
        #     task__contest=self.contest
        # ).values_list('task__index', 'task__name').distinct()
        # context['submission_languages'] = Submission.objects.filter(
        #     user=self.user,
        #     task__contest=self.contest
        # ).values_list('language__key', 'language__name').distinct()
        # context['submission_status'] = Submission.objects.filter(
        #     user=self.user,
        #     task__contest=self.contest
        # ).values_list('status', flat=True).distinct()
        context['submission_status_processing'] = ['QU', 'P', 'G']
        context['submission_result_error'] = ['IE', 'SC', 'AB']

        return context
