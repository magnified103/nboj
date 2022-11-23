import logging

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import RedirectURLMixin
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView

from judge.forms import RegisterForm
from judge.models import Contest, Participation, Task
from judge.utils.util import solved_task

logger = logging.getLogger('judge.views.login')


class LoginView(DjangoLoginView):
    template_name = 'judge/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class LogoutView(DjangoLogoutView):
    pass


class RegisterView(RedirectURLMixin, FormView):
    template_name = 'judge/register.html'
    form_class = RegisterForm
    redirect_authenticated_user = False

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your REGISTER_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)

    def get_default_redirect_url(self):
        """Return the default redirect URL."""
        if self.next_page:
            return resolve_url(self.next_page)
        else:
            return resolve_url(settings.REGISTER_REDIRECT_URL)

    def form_valid(self, form):
        auth_login(self.request, form.save(commit=True))
        return HttpResponseRedirect(self.get_success_url())
