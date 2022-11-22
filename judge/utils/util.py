from django.db import connection
from django.db.models import Max

from judge.models import Submission


def get_best_score(user, task):
    with connection.cursor() as cursor:
        cursor.execute('SELECT COALESCE(MAX(points), 0) FROM judge_submission '
                       'WHERE (user_id = %s AND task_id = %s)', [user.id, task.id])
        return cursor.fetchone()[0]


def solved_task(user, task):
    return get_best_score(user, task) >= task.points
