from django.conf import settings


def asset_version(request):
    return {"ASSET_VERSION": settings.EZMEMORY_ASSET_VERSION}
