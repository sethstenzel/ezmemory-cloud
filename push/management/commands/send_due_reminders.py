"""Push a daily study reminder to every opted-in user with due cards.

Schedule this once or twice a day (cron / Windows Task Scheduler):
    uv run manage.py send_due_reminders
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from flashcards.models import Card
from push.notify import send_to_user


class Command(BaseCommand):
    help = "Send a push reminder to users who have cards due and reminders enabled."

    def handle(self, *args, **options):
        now = timezone.now()
        users = (
            get_user_model()
            .objects.filter(profile__reminders_enabled=True, push_subscriptions__isnull=False)
            .distinct()
        )
        sent = 0
        for user in users:
            due = Card.objects.filter(user=user, due_at__lte=now).count()
            if not due:
                continue
            delivered = send_to_user(
                user,
                title="Time to practice 🧠",
                body=f"You have {due} card{'s' if due != 1 else ''} ready for review.",
                url="/practice/",
            )
            sent += 1 if delivered else 0
        self.stdout.write(self.style.SUCCESS(f"Reminders sent to {sent} user(s)."))
