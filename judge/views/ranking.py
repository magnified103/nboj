from django.db import connection
from django.views.generic import TemplateView

from judge.models import Participation, Submission, Task, User
from judge.utils.util import get_best_score
from judge.views.contest_base import ContestMixin


class RankingView(ContestMixin, TemplateView):
    template_name = 'judge/contest_ranking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # tasks = Task.objects.filter(contest=self.contest).order_by('index')
        tasks = Task.objects.raw('SELECT * FROM judge_task WHERE contest_id = %s '
                                 'ORDER BY judge_task.index ASC', [self.contest.id])

        # user_ids = Participation.objects.filter(contest=self.contest).values_list('user_id', flat=True).distinct()
        user_ids = []
        with connection.cursor() as cursor:
            cursor.execute('SELECT DISTINCT user_id from judge_participation '
                           'WHERE contest_id = %s', [self.contest.id])
            user_ids = [i[0] for i in cursor.fetchall()]

        users = []

        for id in user_ids:
            user = User.objects.get(id=id)
            user.points = []
            user.score = 0
            for task in tasks:
                score = get_best_score(user, task)
                level = 0
                if score == task.points:
                    level = 11
                elif score == 0:
                    level = 0
                else:
                    level = int(score / task.points * 10)
                user.points.append((score, level))
                user.score += score
            with connection.cursor() as cursor:
                cursor.execute('UPDATE judge_participation SET score = %s WHERE '
                               '(contest_id = %s AND user_id = %s)', [user.score, self.contest.id, user.id])
            # Participation.objects.filter(contest=self.contest, user=user).update(score=user.score)
            users.append(user)

        users.sort(key=lambda user: user.score, reverse=True)

        for i in range(len(users)):
            users[i].index = i + 1

        if len(users) > 0:
            max_score = users[0].score
            for user in users:
                user.score_level = 0
                if user.score == max_score:
                    user.score_level = 11
                elif user.score == 0:
                    user.score_level = 0
                else:
                    user.score_level = int(user.score / max_score * 10)

        context['tasks'] = tasks
        context['users'] = users

        return context
