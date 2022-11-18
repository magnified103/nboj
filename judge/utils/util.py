from django.db.models import Max

from judge.models import Submission


def get_best_score(user, task):
    return Submission.objects.filter(
        user=user, task=task).aggregate(Max('points', default=0))['points__max']


def solved_task(user, task):
    return get_best_score(user, task) >= task.points
