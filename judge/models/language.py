from collections import OrderedDict, defaultdict
from operator import attrgetter

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import CASCADE
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    key = models.CharField(max_length=6, verbose_name=_('short identifier'),
                           help_text=_('The identifier for this language; the same as its executor id for judges.'),
                           unique=True)
    name = models.CharField(max_length=20, verbose_name=_('long name'),
                            help_text=_('Longer name for the language, e.g. "Python 2" or "C++11".'))
    short_name = models.CharField(max_length=10, verbose_name=_('short name'),
                                  help_text=_('More readable, but short, name to display publicly; e.g. "PY2" or '
                                              '"C++11". If left blank, it will default to the '
                                              'short identifier.'),
                                  null=True, blank=True)
    common_name = models.CharField(max_length=10, verbose_name=_('common name'),
                                   help_text=_('Common name for the language. For example, the common name for C++03, '
                                               'C++11, and C++14 would be "C++".'))
    ace = models.CharField(max_length=20, verbose_name=_('ace mode name'),
                           help_text=_('Language ID for Ace.js editor highlighting, appended to "mode-" to determine '
                                       'the Ace JavaScript file to use, e.g., "python".'))
    pygments = models.CharField(max_length=20, verbose_name=_('pygments name'),
                                help_text=_('Language ID for Pygments highlighting in source windows.'))
    template = models.TextField(verbose_name=_('code template'),
                                help_text=_('Code template to display in submission editor.'), blank=True)
    info = models.CharField(max_length=50, verbose_name=_('runtime info override'), blank=True,
                            help_text=_("Do not set this unless you know what you're doing! It will override the "
                                        'usually more specific, judge-provided runtime info!'))
    description = models.TextField(verbose_name=_('language description'),
                                   help_text=_('Use this field to inform users of quirks with your environment, '
                                               'additional restrictions, etc.'), blank=True)
    extension = models.CharField(max_length=10, verbose_name=_('extension'),
                                 help_text=_('The extension of source files, e.g., "py" or "cpp".'))

    @classmethod
    def get_common_name_map(cls):
        result = cache.get('lang:cn_map')
        if result is not None:
            return result
        result = defaultdict(set)
        for id, cn in Language.objects.values_list('id', 'common_name'):
            result[cn].add(id)
        result = {id: cns for id, cns in result.items() if len(cns) > 1}
        cache.set('lang:cn_map', result, 86400)
        return result

    @cached_property
    def short_display_name(self):
        return self.short_name or self.key

    def __str__(self):
        return self.name

    @cached_property
    def display_name(self):
        if self.info:
            return '%s (%s)' % (self.name, self.info)
        else:
            return self.name

    @classmethod
    def get_python3(cls):
        # We really need a default language, and this app is in Python 3
        return Language.objects.get_or_create(key='PY3', defaults={'name': 'Python 3'})[0]

    def get_absolute_url(self):
        return reverse('runtime_list') + '#' + self.key

    @classmethod
    def get_default_language(cls):
        try:
            return Language.objects.get(key=settings.DEFAULT_USER_LANGUAGE)
        except Language.DoesNotExist:
            return cls.get_python3()

    @classmethod
    def get_default_language_pk(cls):
        return cls.get_default_language().pk

    class Meta:
        ordering = ['key']
        verbose_name = _('language')
        verbose_name_plural = _('languages')
