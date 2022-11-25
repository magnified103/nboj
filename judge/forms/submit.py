from urllib.parse import urljoin

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.models import ModelChoiceIteratorValue
from django.forms.utils import flatatt
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_ace import AceWidget

from judge.models import Language, Submission


class CodeWidget(AceWidget):
    def __init__(self, id=None, use_required_attribute=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id
        self._use_required_attribute = use_required_attribute

    @property
    def media(self):
        js = [urljoin(settings.ACE_URL, 'ace.js'), static("django_ace/widget.js")]

        if self.mode:
            js.append(urljoin(settings.ACE_URL, "mode-%s.js" % self.mode))
        if self.theme:
            js.append(urljoin(settings.ACE_URL, "theme-%s.js" % self.theme))

        css = {"screen": ["django_ace/widget.css"]}

        return forms.Media(js=js, css=css)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}

        ace_attrs = {
            "class": "django-ace-widget loading",
            "style": "width:%s; height:%s" % (self.width, self.height),
        }

        if self.mode:
            ace_attrs["data-mode"] = self.mode
        if self.theme:
            ace_attrs["data-theme"] = self.theme
        if self.wordwrap:
            ace_attrs["data-wordwrap"] = "true"
        if self.minlines:
            ace_attrs["data-minlines"] = str(self.minlines)
        if self.maxlines:
            ace_attrs["data-maxlines"] = str(self.maxlines)
        if self.tabsize:
            ace_attrs["data-tabsize"] = str(self.tabsize)
        if self.fontsize:
            ace_attrs["data-fontsize"] = str(self.fontsize)
        if self.id:
            ace_attrs["id"] = str(self.id)

        ace_attrs["data-readonly"] = "true" if self.readonly else "false"
        ace_attrs["data-showgutter"] = "true" if self.showgutter else "false"
        ace_attrs["data-behaviours"] = "true" if self.behaviours else "false"
        ace_attrs["data-showprintmargin"] = "true" if self.showprintmargin else "false"
        ace_attrs["data-showinvisibles"] = "true" if self.showinvisibles else "false"
        ace_attrs["data-usesofttabs"] = "true" if self.usesofttabs else "false"

        textarea = super(AceWidget, self).render(name, value, attrs, renderer)

        html = "<div{}><div></div></div>{}".format(flatatt(ace_attrs), textarea)

        if self.toolbar:
            toolbar = (
                '<div style="width: {}" class="django-ace-toolbar">'
                '<a href="./" class="django-ace-max_min"></a>'
                "</div>"
            ).format(self.width)
            html = toolbar + html

        html = '<div class="django-ace-editor">{}</div>'.format(html)
        return mark_safe(html)

    def use_required_attribute(self, initial):
        return super().use_required_attribute(initial) and self._use_required_attribute


class LanguageSelectWidget(forms.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if isinstance(value, ModelChoiceIteratorValue):
            language = value.instance
            option['attrs'].update({
                'data-id': language.key,
                'data-name': language.name,
                'data-ace': language.ace,
            })
            option['label'] = language.name
        else:
            option['value'] = ''

        return option


class TaskSelectWidget(forms.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if isinstance(value, ModelChoiceIteratorValue):
            task = value.instance
            option['label'] = task.name
        else:
            option['value'] = ''

        return option


class EditorForm(forms.ModelForm):

    def __init__(self, task, language, initial_task=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['language'].queryset = language
        self.fields['task'].queryset = task
        if initial_task is not None:
            self.fields['task'].initial = initial_task
            self.fields['task'].disabled = True
        # if selected_task is not None:
        #     self.fields['task'].disabled = True

        if 'task' in self.errors:
            classes = self.fields['task'].widget.attrs.get('class', '')
            classes += ' is-invalid'
            self.fields['task'].widget.attrs['class'] = classes

        if 'language' in self.errors:
            classes = self.fields['language'].widget.attrs.get('class', '')
            classes += ' is-invalid'
            self.fields['language'].widget.attrs['class'] = classes

    def clean(self):
        cleaned_data = super().clean()
        task = cleaned_data.get('task')
        language = cleaned_data.get('language')

        if task and language and not task.allowed_languages.filter(id=language.id).exists():
            self.add_error('language', ValidationError(
                _('Allowed language for %(task)s: [%(languages)s]'),
                params={
                    'task': task.name,
                    'languages': ', '.join(list(task.allowed_languages.all().values_list('name', flat=True))),
                },
                code='invalid'
            ))

    class Meta:
        model = Submission
        fields = ['source', 'task', 'language']
        field_classes = {
            'source': forms.CharField,
            'task': forms.ModelChoiceField,
            'language': forms.ModelChoiceField,
        }
        widgets = {
            'source': CodeWidget(id='ace_source', use_required_attribute=False, width='100%', showprintmargin=False),
            'task': TaskSelectWidget(attrs={
                'class': 'form-control select2bs4',
                'style': 'width: 100%',
            }),
            'language': LanguageSelectWidget(attrs={
                'id': 'id_language',
                'class': 'form-control select2bs4',
                'style': 'width: 100%',
            }),
        }
