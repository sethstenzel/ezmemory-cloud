"""Send Web Push notifications to a user's registered devices."""

import json
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

from .vapid import KEY_PATH, get_vapid

logger = logging.getLogger(__name__)


def send_to_user(user, title, body, url="/"):
    """Push to every device the user registered. Returns the delivered count.

    Dead subscriptions (endpoint gone: HTTP 404/410) are pruned automatically.
    """
    get_vapid()  # ensure the key file exists before pywebpush reads it
    payload = json.dumps({"title": title, "body": body, "url": url})
    delivered = 0
    for subscription in list(user.push_subscriptions.all()):
        try:
            webpush(
                subscription_info=subscription.as_webpush_info(),
                data=payload,
                vapid_private_key=str(KEY_PATH),
                vapid_claims={"sub": settings.EZMEMORY_VAPID_CLAIM},
            )
            delivered += 1
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (404, 410):
                subscription.delete()
            else:
                logger.warning("Push to %s failed: %s", subscription.endpoint[:60], exc)
    return delivered
