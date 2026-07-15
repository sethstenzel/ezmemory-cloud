from django.shortcuts import redirect

from .models import profile_for

# Paths reachable after a trial expires: account pages, public content, the
# subscribe page itself, and PWA plumbing.
EXEMPT_PREFIXES = (
    "/login",
    "/logout",
    "/signup",
    "/subscribe",
    "/settings",
    "/blog",
    "/tutorials",
    "/admin",
    "/static",
    "/sw.js",
    "/manifest.webmanifest",
)


class TrialAccessMiddleware:
    """Redirect users whose 30-day trial has ended (and who haven't subscribed)
    to the subscribe page. Their data is kept; access resumes on subscription."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith(EXEMPT_PREFIXES):
            if not profile_for(request.user).has_access:
                return redirect("subscribe")
        return self.get_response(request)
