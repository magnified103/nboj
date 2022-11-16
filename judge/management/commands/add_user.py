from django.core.management.base import BaseCommand

from judge.models import User


class Command(BaseCommand):
    help = 'creates a user'

    def add_arguments(self, parser):
        parser.add_argument('name', help='username')
        parser.add_argument('email', help='email, not necessary to be resolvable')
        parser.add_argument('password', help='password for the user')

        parser.add_argument('--superuser', action='store_true', default=False,
                            help='if specified, creates user with superuser privileges')
        parser.add_argument('--staff', action='store_true', default=False,
                            help='if specified, creates user with staff privileges')

    def handle(self, *args, **options):
        user = User(username=options['name'], email=options['email'], is_active=True)
        user.set_password(options['password'])
        user.is_superuser = options['superuser']
        user.is_staff = options['staff']
        user.save()

