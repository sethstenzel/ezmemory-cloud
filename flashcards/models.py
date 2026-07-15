from django.conf import settings
from django.db import models
from django.utils import timezone

from notes.models import Node


class Card(models.Model):
    class Kind(models.TextChoices):
        FORWARD = "forward", "Forward"
        REVERSE = "reverse", "Reverse"
        CLOZE = "cloze", "Cloze"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="cards")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    cloze_index = models.PositiveIntegerField(default=0)
    front = models.TextField()
    back = models.TextField()

    # SM-2 scheduling state
    ease = models.FloatField(default=2.5)
    interval = models.FloatField(default=0)  # days
    repetitions = models.PositiveIntegerField(default=0)
    due_at = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_at"]
        unique_together = [("node", "kind", "cloze_index")]

    def __str__(self):
        return f"{self.front[:40]} [{self.kind}]"

    @property
    def is_due(self):
        return self.due_at <= timezone.now()

    @property
    def is_new(self):
        return self.repetitions == 0 and self.interval == 0

    RATING_AGAIN = 0
    RATING_HARD = 3
    RATING_GOOD = 4
    RATING_EASY = 5

    def apply_rating(self, rating):
        """SM-2 style scheduling update."""
        now = timezone.now()
        if rating == self.RATING_AGAIN:
            self.repetitions = 0
            self.interval = 0
            self.ease = max(1.3, self.ease - 0.2)
            self.due_at = now + timezone.timedelta(minutes=10)
        else:
            if rating == self.RATING_HARD:
                self.ease = max(1.3, self.ease - 0.15)
                self.interval = max(1.0, self.interval * 1.2)
            elif rating == self.RATING_GOOD:
                if self.repetitions == 0:
                    self.interval = 1.0
                elif self.repetitions == 1:
                    self.interval = 6.0
                else:
                    self.interval = self.interval * self.ease
            else:  # easy
                self.ease += 0.15
                self.interval = max(2.0, self.interval * self.ease * 1.3) if self.interval else 4.0
            self.repetitions += 1
            self.due_at = now + timezone.timedelta(days=self.interval)
        self.save()
        ReviewLog.objects.create(card=self, rating=rating, interval_after=self.interval, ease_after=self.ease)
        # Keep history bounded: only the 10 most recent reviews per card.
        stale = ReviewLog.objects.filter(card=self).values_list("id", flat=True)[10:]
        if stale:
            ReviewLog.objects.filter(id__in=list(stale)).delete()


class ReviewLog(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    interval_after = models.FloatField()
    ease_after = models.FloatField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reviewed_at"]
