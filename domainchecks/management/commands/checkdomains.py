from django.core.management import BaseCommand

from ...models import DomainCheck


class Command(BaseCommand):
    help = 'Pings configured domain checks for their current status.'

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        if verbosity > 0:
            self.stdout.write('Refreshing domain statuses\n')
        count = 0
        for check in DomainCheck.objects.active().stale():
            if verbosity > 1:
                self.stdout.write('Running check {}\n'.format(check))
            check.run_check()
            count += 1
        if verbosity > 0:
            self.stdout.write('{count} domain status{plural} updated\n'.format(
                count=count, plural='' if count == 1 else 'es'))
