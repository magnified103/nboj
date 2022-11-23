from django import forms

from judge.models import Submission


class SubmissionFilterForm(forms.Form):
    task_filter = forms.ChoiceField(required=False)
    language_filter = forms.ChoiceField(required=False)
    status_filter = forms.ChoiceField(required=False)

    def __init__(self, user, contest, initial_task=None, initial_language=None, initial_status=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['task_filter'].widget = forms.Select(attrs={
            'id': 'filter-task',
            'class': 'form-control input-sm w-100',
        })
        self.fields['task_filter'].choices = [('', '---------'), *list(Submission.objects.filter(
            user=user,
            task__contest=contest
        ).values_list('task__index', 'task__name').distinct())]
        self.fields['task_filter'].initial = initial_task
        self.fields['language_filter'].widget = forms.Select(attrs={
            'id': 'filter-language',
            'class': 'form-control input-sm w-100',
        })
        self.fields['language_filter'].choices = [('', '---------'), *list(Submission.objects.filter(
            user=user,
            task__contest=contest
        ).values_list('language__key', 'language__name').distinct())]
        self.fields['language_filter'].initial = initial_language
        self.fields['status_filter'].widget = forms.Select(attrs={
            'id': 'filter-status',
            'class': 'form-control input-sm w-100',
        })
        self.fields['status_filter'].choices = [('', '---------'), *list(Submission.objects.filter(
            user=user,
            task__contest=contest
        ).values_list('result', 'result').distinct())]
        self.fields['status_filter'].initial = initial_status
