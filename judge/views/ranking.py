from django.db.models import Max

from judge.models import Participation, Submission, Task, User
from judge.utils.util import get_best_score
from judge.views.contest_base import ContestBaseView


class RankingView(ContestBaseView):
    template_name = 'judge/contest_ranking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tasks = Task.objects.filter(contest=self.contest).order_by('index')

        user_ids = Participation.objects.filter(contest=self.contest).values_list('user_id', flat=True).distinct()
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
            Participation.objects.filter(contest=self.contest, user=user).update(score=user.score)
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
