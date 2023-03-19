from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from judge.models import Attachment, Contest, Task, User, Submission, Language, Judge, Participation, TaskData


class AttachmentInline(admin.TabularInline):
    model = Attachment
    fk_name = 'task'
    extra = 0


class TaskAdmin(admin.ModelAdmin):
    inlines = [
        AttachmentInline,
    ]


class ParticipationInline(admin.TabularInline):
    model = Participation
    fk_name = 'contest'
    extra = 0
    fields = ['user']


class ContestAdmin(admin.ModelAdmin):
    inlines = [
        ParticipationInline
    ]


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'task']


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Contest, ContestAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Judge)
admin.site.register(Language)
admin.site.register(TaskData)
