import math

from django.conf import settings
from django.db import models


class BlogPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_posts")
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(help_text="Short teaser shown on the blog index cards.")
    body = models.TextField(help_text="Markdown body.")
    emoji = models.CharField(max_length=8, default="📚", help_text="Card artwork placeholder.")
    featured = models.BooleanField(default=False)
    published_at = models.DateField()

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    @property
    def reading_minutes(self):
        return max(1, math.ceil(len(self.body.split()) / 200))


class TutorialCollection(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=8, default="📖")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title


class TutorialArticle(models.Model):
    collection = models.ForeignKey(TutorialCollection, on_delete=models.CASCADE, related_name="articles")
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(blank=True)
    body = models.TextField(help_text="Markdown body.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title
