from urllib.request import urlopen

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.views.generic import View

from judge.models import Attachment, Participation, Task


class AttachmentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        try:
            task = Task.objects.get(id=self.kwargs['task_id'])
            user = self.request.user
            if Participation.objects.filter(contest=task.contest, user=user).count() == 0:
                return False
            return Attachment.objects.filter(task=task, name=self.kwargs['attachment_name']).count() > 0
        except Task.DoesNotExist:
            return False

    def get(self, request, *args, **kwargs):
        try:
            task = Task.objects.get(id=self.kwargs['task_id'])
            user = self.request.user
            if Participation.objects.filter(contest=task.contest, user=user).count() == 0:
                raise PermissionDenied()
            attachment_name = self.kwargs['attachment_name']
            return FileResponse(
                urlopen(Attachment.objects.get(task=task, name=attachment_name).path),
                filename=attachment_name
            )
        except Exception:
            raise PermissionDenied()
