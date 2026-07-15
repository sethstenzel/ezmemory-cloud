"""VAPID key management for Web Push.

Keys are generated once on first use and stored in BASE_DIR/vapid_private_key.pem
(gitignored). The public application-server key is derived from it for the browser.
"""

import base64
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from django.conf import settings
from py_vapid import Vapid

KEY_PATH = settings.BASE_DIR / "vapid_private_key.pem"


@lru_cache(maxsize=1)
def get_vapid():
    if not KEY_PATH.exists():
        vapid = Vapid()
        vapid.generate_keys()
        vapid.save_key(str(KEY_PATH))
    return Vapid.from_file(str(KEY_PATH))


def public_application_server_key():
    """Base64url-encoded uncompressed EC point, as pushManager.subscribe expects."""
    raw = get_vapid().public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
