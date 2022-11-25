from ansi2html import Ansi2HTMLConverter
from django.utils.functional import cached_property
from django.views.generic import TemplateView
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from judge.models import Submission
from judge.views.contest_base import ContestMixin


class SubmissionView(ContestMixin, TemplateView):
    template_name = 'judge/contest_submission.html'

    @cached_property
    def submission(self):
        if 'submission_id' in self.kwargs:
            return Submission.objects.get(id=self.kwargs['submission_id'])
        raise Submission.DoesNotExist()

    def test_func(self):
        if not super().test_func():
            return False
        try:
            return self.submission.user == self.user
        except Exception:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submission'] = self.submission

        context['cases'] = self.submission.cases

        context['error'] = '' if not self.submission.error else Ansi2HTMLConverter().convert(self.submission.error)

        lexer = get_lexer_by_name(self.submission.language.pygments)
        formatter = HtmlFormatter(linenos=True)
        context['source'] = highlight(self.submission.source, lexer, formatter)
        context['source_style'] = formatter.get_style_defs('.highlight')

        context['submission_status_processing'] = ['QU', 'P', 'G']
        context['submission_result_error'] = ['IE', 'SC', 'AB']

        return context
