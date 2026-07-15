from django.contrib import admin

from .models import BlogPost, TutorialArticle, TutorialCollection


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "featured", "published_at")
    list_filter = ("featured",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TutorialCollection)
class TutorialCollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TutorialArticle)
class TutorialArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "collection", "order")
    list_filter = ("collection",)
    prepopulated_fields = {"slug": ("title",)}
