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

from judge.judgeapi import disconnect_judge
from judge.models.language import Language
from judge.models.task import TaskData


# class RuntimeVersion(models.Model):
#     language = models.ForeignKey(Language, verbose_name=_('language to which this runtime belongs'), on_delete=CASCADE)
#     judge = models.ForeignKey('Judge', verbose_name=_('judge on which this runtime exists'), on_delete=CASCADE)
#     name = models.CharField(max_length=64, verbose_name=_('runtime name'))
#     version = models.CharField(max_length=64, verbose_name=_('runtime version'), blank=True)
#     priority = models.IntegerField(verbose_name=_('order in which to display this runtime'), default=0)


class Judge(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('judge name'), help_text=_('Server name, hostname-style.'),
                            unique=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('time of creation'))
    auth_key = models.CharField(max_length=100, help_text=_('A key to authenticate this judge.'),
                                verbose_name=_('authentication key'))
    is_blocked = models.BooleanField(verbose_name=_('block judge'), default=False,
                                     help_text=_('Whether this judge should be blocked from connecting, '
                                                 'even if its key is correct.'))
    online = models.BooleanField(verbose_name=_('judge online status'), default=False)
    start_time = models.DateTimeField(verbose_name=_('judge start time'), null=True)
    ping = models.FloatField(verbose_name=_('response time'), null=True)
    load = models.FloatField(verbose_name=_('system load'), null=True,
                             help_text=_('Load for the last minute, divided by processors to be fair.'))
    description = models.TextField(blank=True, verbose_name=_('description'))
    last_ip = models.GenericIPAddressField(verbose_name=_('last connected IP'), blank=True, null=True)
    tasks = models.ManyToManyField(TaskData, verbose_name=_('problems'), related_name='judges')
    runtimes = models.ManyToManyField(Language, verbose_name=_('judges'), related_name='judges')

    def __str__(self):
        return self.name

    def disconnect(self, force=False):
        disconnect_judge(self, force=force)

    disconnect.alters_data = True

    @cached_property
    def uptime(self):
        return timezone.now() - self.start_time if self.online else 'N/A'

    @cached_property
    def ping_ms(self):
        return self.ping * 1000 if self.ping is not None else None

    @cached_property
    def runtime_list(self):
        return map(attrgetter('name'), self.runtimes.all())

    class Meta:
        ordering = ['name']
        verbose_name = _('judge')
        verbose_name_plural = _('judges')