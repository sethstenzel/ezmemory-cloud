from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.core.cache import cache
from django.shortcuts import redirect, render


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
