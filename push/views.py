import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from .models import PushSubscription
from .notify import send_to_user
from .vapid import public_application_server_key


def service_worker(request):
    """Serve the service worker from the site root so its scope covers '/'."""
    path = finders.find("js/sw.js")
    with open(path, "rb") as fh:
        return HttpResponse(fh.read(), content_type="application/javascript")


def manifest(request):
    return JsonResponse(
        {
            "name": "ezmemory",
            "short_name": "ezmemory",
            "description": "Notes that quiz you back.",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#1c2130",
            "theme_color": "#4f46e5",
            "icons": [
                {"src": "/static/img/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}
            ],
        },
        content_type="application/manifest+json",
    )


@login_required
def vapid_public_key(request):
    return JsonResponse({"key": public_application_server_key()})


@login_required
@require_POST
def subscribe(request):
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data["keys"]
        p256dh, auth = keys["p256dh"], keys["auth"]
    except (ValueError, KeyError):
        return HttpResponse("Invalid subscription payload.", status=400, content_type="text/plain")
    if len(endpoint) > 1000:
        return HttpResponse("Invalid subscription payload.", status=400, content_type="text/plain")

    existing = PushSubscription.objects.filter(endpoint=endpoint).first()
    if existing and existing.user_id != request.user.id:
        existing.delete()  # device changed hands; re-register under the new account
        existing = None
    if existing is None:
        if request.user.push_subscriptions.count() >= settings.EZMEMORY_MAX_PUSH_DEVICES_PER_USER:
            return HttpResponse(
                "Device limit reached. Remove a device in Settings first.",
                status=400,
                content_type="text/plain",
            )
        PushSubscription.objects.create(
            user=request.user,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    else:
        existing.p256dh, existing.auth = p256dh, auth
        existing.save(update_fields=["p256dh", "auth"])
    return JsonResponse({"ok": True, "devices": request.user.push_subscriptions.count()})


@login_required
@require_POST
def unsubscribe(request):
    try:
        data = json.loads(request.body)
        endpoint = data.get("endpoint", "")
    except ValueError:
        endpoint = ""
    if endpoint:
        request.user.push_subscriptions.filter(endpoint=endpoint).delete()
    else:
        request.user.push_subscriptions.all().delete()
    return JsonResponse({"ok": True, "devices": request.user.push_subscriptions.count()})


@login_required
@require_POST
def send_test(request):
    delivered = send_to_user(
        request.user,
        title="ezmemory test notification",
        body="Push notifications are working on this device. 🎉",
        url="/practice/",
    )
    return JsonResponse({"ok": True, "delivered": delivered})
