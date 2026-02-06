from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJobExecution
from notifications.scheduler import delete_old_notifications


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone="UTC")
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            delete_old_notifications,
            trigger="interval",
            hours=24,
            id="delete_old_notifications",
            replace_existing=True,
        )

        register_events(scheduler)

        self.stdout.write(self.style.SUCCESS("Scheduler started..."))

        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.shutdown()
            self.stdout.write(self.style.SUCCESS("Scheduler stopped."))
