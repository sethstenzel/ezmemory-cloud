from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_subscribed", "trial_ends_at", "trial_days_left", "reminders_enabled", "created_at")
    list_filter = ("is_subscribed", "reminders_enabled")
    search_fields = ("user__username",)
    actions = ["activate_subscription", "deactivate_subscription"]

    @admin.action(description="Mark selected profiles as subscribed")
    def activate_subscription(self, request, queryset):
        from django.utils import timezone

        queryset.update(is_subscribed=True, subscribed_at=timezone.now())

    @admin.action(description="Remove subscription from selected profiles")
    def deactivate_subscription(self, request, queryset):
        queryset.update(is_subscribed=False, subscribed_at=None)
