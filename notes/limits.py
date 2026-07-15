"""Per-account content quotas. ezmemory stores text only; these caps bound the
storage any single account can consume."""

from django.conf import settings

from .models import Document, Folder, Node


def clamp_node_text(text):
    return text[: settings.EZMEMORY_MAX_NODE_TEXT_CHARS]


def clamp_title(title):
    return title[: settings.EZMEMORY_MAX_DOC_TITLE_CHARS]


def node_quota_left(user):
    return settings.EZMEMORY_MAX_NODES_PER_USER - Node.objects.filter(document__user=user).count()


def document_quota_left(user):
    return settings.EZMEMORY_MAX_DOCUMENTS_PER_USER - Document.objects.filter(user=user).count()


def folder_quota_left(user):
    return settings.EZMEMORY_MAX_FOLDERS_PER_USER - Folder.objects.filter(user=user).count()


NODE_QUOTA_MESSAGE = "You've reached the note limit for your account, so this bullet wasn't added. Delete some notes to free up space."
DOCUMENT_QUOTA_MESSAGE = "You've reached the document limit for your account. Delete a document to create a new one."
FOLDER_QUOTA_MESSAGE = "You've reached the topic limit for your account. Delete a topic to create a new one."
