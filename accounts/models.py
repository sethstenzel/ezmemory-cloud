from django.conf import settings
from django.db import models
from django.utils import timezone


def default_trial_end():
    return timezone.now() + timezone.timedelta(days=30)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    trial_ends_at = models.DateTimeField(default=default_trial_end)
    is_subscribed = models.BooleanField(default=False, help_text="Paid subscription is active.")
    subscribed_at = models.DateTimeField(null=True, blank=True)
    reminders_enabled = models.BooleanField(default=False, help_text="Send daily due-card push reminders.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} profile"

    @property
    def on_trial(self):
        return not self.is_subscribed and timezone.now() <= self.trial_ends_at

    @property
    def trial_days_left(self):
        remaining = self.trial_ends_at - timezone.now()
        if remaining.total_seconds() <= 0:
            return 0
        return remaining.days + (1 if remaining.seconds else 0)

    @property
    def has_access(self):
        return self.is_subscribed or self.user.is_staff or timezone.now() <= self.trial_ends_at


def profile_for(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile
