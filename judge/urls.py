from django.urls import path

from judge.views import AttachmentView, DashboardView, ContestView, LoginView, LogoutView, RankingView, RegisterView
from judge.views import SubmissionListView
from judge.views import SubmitView, TaskView, TestView

urlpatterns = [
    path('contests/', DashboardView.as_view(), name='contests'),
    path('contest/<int:contest_id>/', ContestView.as_view(), name='contest'),
    path('task/<int:task_id>/', TaskView.as_view(), name='task'),
    path('contest/<int:contest_id>/task/<str:task_index>/', TaskView.as_view(), name='contest_task'),
    path('task/<int:task_id>/attachment/<str:attachment_name>/', AttachmentView.as_view(), name='attachment'),
    path('login/', LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('register/', RegisterView.as_view(redirect_authenticated_user=True), name='register'),
    path('task/<int:task_id>/submit', SubmitView.as_view(), name='submit_task'),
    path('contest/<int:contest_id>/submit/', SubmitView.as_view(), name='submit'),
    path('contest/<int:contest_id>/submissions/', SubmissionListView.as_view(), name='submissions'),
    path('contest/<int:contest_id>/ranking', RankingView.as_view(), name='ranking'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('test', TestView.as_view(), name='test')
]
