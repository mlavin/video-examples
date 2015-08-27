import datetime

from celery import group, shared_task
from celery.utils.log import get_task_logger

from . import models


logger = get_task_logger(__name__)


@shared_task
def check_domain(name, minutes=10, timeout=10):
    """Run active and stale checks for the given domain."""
    cutoff = datetime.timedelta(minutes=minutes)
    checks = models.DomainCheck.objects.active().stale(cutoff=cutoff).filter(
        domain__name=name).select_related('domain')
    count = 0
    for check in checks:
        logger.debug('Running check %s', check)
        check.run_check(timeout=timeout)
        count += 1
    logger.info('Completed %d check(s) for %s', count, name)


@shared_task
def queue_domains(minutes=10, timeout=10):
    """Queue domains to be checked."""
    domains = models.DomainCheck.objects.active().values_list(
        'domain__name', flat=True).distinct()
    subtasks = group(*(
        check_domain.s(name, minutes=minutes, timeout=timeout)
        for name in domains))
    subtasks.delay()
