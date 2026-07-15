from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Profile, profile_for


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    throttle_key = f"signup-count:{client_ip(request)}"
    if request.method == "POST":
        if cache.get(throttle_key, 0) >= settings.EZMEMORY_SIGNUPS_PER_IP_PER_HOUR:
            form = UserCreationForm(request.POST)
            return render(
                request,
                "accounts/signup.html",
                {"form": form, "throttled": "Too many accounts were created from your network recently. Please try again in an hour."},
            )
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)  # starts the 30-day trial
            try:
                cache.add(throttle_key, 0, timeout=3600)
                cache.incr(throttle_key)
            except ValueError:
                pass
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def subscribe(request):
    return render(request, "accounts/subscribe.html", {"profile": profile_for(request.user)})


@login_required
def user_settings(request):
    return render(request, "accounts/settings.html", {"profile": profile_for(request.user)})


@login_required
@require_POST
def toggle_reminders(request):
    profile = profile_for(request.user)
    profile.reminders_enabled = request.POST.get("enabled") == "1"
    profile.save(update_fields=["reminders_enabled"])
    return render(request, "accounts/_reminders_toggle.html", {"profile": profile})
