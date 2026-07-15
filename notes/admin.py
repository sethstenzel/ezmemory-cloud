from django.contrib import admin

from .models import Document, Folder, Node


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "folder", "is_daily", "daily_date", "updated_at")
    list_filter = ("is_daily",)
    search_fields = ("title",)


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("text", "document", "parent", "position")
    search_fields = ("text",)
