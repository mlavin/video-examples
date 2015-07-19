import datetime

from django.core.management import BaseCommand

from ...models import DomainCheck


class Command(BaseCommand):
    help = 'Pings configured domain checks for their current status.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes', type=int, dest='minutes', default=5,
            help='Time cutoff from the last check (in minutes).')
        parser.add_argument(
            '--timeout', type=int, dest='timeout', default=10,
            help='Timeout for server response (in seconds).')

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        if verbosity > 0:
            self.stdout.write('Refreshing domain statuses\n')
        count = 0
        cutoff = datetime.timedelta(minutes=options['minutes'])
        for check in DomainCheck.objects.active().stale(cutoff=cutoff):
            if verbosity > 1:
                self.stdout.write('Running check {}\n'.format(check))
            check.run_check(timeout=options['timeout'])
            count += 1
        if verbosity > 0:
            self.stdout.write('{count} domain status{plural} updated\n'.format(
                count=count, plural='' if count == 1 else 'es'))
