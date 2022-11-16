from django.contrib.auth.views import LoginView
from django.urls import path

from judge.views import AttachmentView, ContestListView, ContestView, SubmitView, TaskView, TestView

urlpatterns = [
    path('contests/', ContestListView.as_view(), name='contests'),
    path('contest/<int:contest_id>/', ContestView.as_view(), name='contest'),
    path('task/<int:task_id>/', TaskView.as_view(), name='task'),
    path('task/<int:task_id>/attachment/<str:attachment_name>/', AttachmentView.as_view(), name='attachment'),
    path('login/', LoginView.as_view(template_name='admin/login.html', redirect_authenticated_user=True,
                                     extra_context={'site_header': 'Login portal'}), name='login'),
    path('task/<int:task_id>/submit', SubmitView.as_view(), name='submit_task'),
    path('contest/<int:contest_id>/submit', SubmitView.as_view(), name='submit'),
    path('test', TestView.as_view(), name='test')
]
