import logging

import django.contrib.auth.views as django_views
from django.contrib.auth.forms import AuthenticationForm
from django.utils.functional import cached_property

from judge.models import Contest, Participation, Task
from judge.utils.util import solved_task

logger = logging.getLogger('judge.views.login')


class LoginView(django_views.LoginView):
    template_name = 'judge/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class LogoutView(django_views.LogoutView):
    pass
