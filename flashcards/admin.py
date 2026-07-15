from django.contrib import admin

from .models import Card, ReviewLog


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("front", "kind", "user", "due_at", "interval", "ease", "repetitions")
    list_filter = ("kind",)
    search_fields = ("front", "back")


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ("card", "rating", "interval_after", "reviewed_at")
