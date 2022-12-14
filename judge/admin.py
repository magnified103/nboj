from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from judge.models import Attachment, Contest, Task, User, Submission, Language, Judge


class AttachmentInline(admin.TabularInline):
    model = Attachment
    fk_name = 'task'
    extra = 0


class TaskAdmin(admin.ModelAdmin):
    inlines = [
        AttachmentInline,
    ]


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Contest)
admin.site.register(Submission)
admin.site.register(Judge)
admin.site.register(Language)
