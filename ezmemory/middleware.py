from django.conf import settings
from django.http import HttpResponse


class BlockUploadsMiddleware:
    """Reject file uploads and oversized request bodies at the door.

    ezmemory is text-only: no view reads request.FILES. Two gates enforce that
    cheaply:

    1. Any request body over DATA_UPLOAD_MAX_MEMORY_SIZE is rejected from its
       Content-Length header alone, before the body is read. (Django's own
       check excludes file parts of multipart bodies; this one does not, so
       big media blobs are refused no matter how they're wrapped.)
    2. A multipart request that fits the cap but contains file parts (the only
       way to send a PDF/image/video) is rejected after parsing at most 256 KB.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            content_length = int(request.META.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            content_length = 0
        if content_length > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
            return HttpResponse(
                "Request body too large.", status=413, content_type="text/plain"
            )
        if request.content_type == "multipart/form-data" and request.FILES:
            return HttpResponse(
                "File uploads are not supported. ezmemory stores text only.",
                status=413,
                content_type="text/plain",
            )
        return self.get_response(request)
