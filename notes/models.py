from django.conf import settings
from django.db import models


class Folder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("user", "name")]

    def __str__(self):
        return self.name


class Document(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    title = models.CharField(max_length=300)
    is_daily = models.BooleanField(default=False)
    daily_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "daily_date"],
                condition=models.Q(is_daily=True),
                name="unique_daily_document_per_day",
            )
        ]

    def __str__(self):
        return self.title


class Node(models.Model):
    """One bullet in a document's outline."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="nodes")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    position = models.PositiveIntegerField(default=0)
    text = models.TextField(blank=True)
    collapsed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.text[:60]

    def siblings(self):
        return Node.objects.filter(document=self.document, parent=self.parent)

    def previous_sibling(self):
        return self.siblings().filter(position__lt=self.position).order_by("-position").first()
