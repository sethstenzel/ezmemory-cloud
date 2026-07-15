from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views as accounts_views
from content import views as content_views
from flashcards import views as flashcards_views
from notes import views as notes_views
from push import views as push_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth & account
    path("signup/", accounts_views.signup, name="signup"),
    path("subscribe/", accounts_views.subscribe, name="subscribe"),
    path("settings/", accounts_views.user_settings, name="user_settings"),
    path("settings/reminders/", accounts_views.toggle_reminders, name="toggle_reminders"),

    # Push notifications & PWA
    path("push/key/", push_views.vapid_public_key, name="push_key"),
    path("push/subscribe/", push_views.subscribe, name="push_subscribe"),
    path("push/unsubscribe/", push_views.unsubscribe, name="push_unsubscribe"),
    path("push/test/", push_views.send_test, name="push_test"),
    path("sw.js", push_views.service_worker, name="service_worker"),
    path("manifest.webmanifest", push_views.manifest, name="manifest"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html", redirect_authenticated_user=True),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # App
    path("", notes_views.home, name="home"),
    path("daily/", notes_views.daily_today, name="daily_today"),
    path("d/<int:pk>/", notes_views.document_detail, name="document_detail"),
    path("d/open/", notes_views.document_open, name="document_open"),
    path("d/create/", notes_views.document_create, name="document_create"),
    path("d/<int:pk>/rename/", notes_views.document_rename, name="document_rename"),
    path("d/<int:pk>/delete/", notes_views.document_delete, name="document_delete"),
    path("d/<int:pk>/move/", notes_views.document_move, name="document_move"),
    path("documents/", notes_views.document_list, name="document_list"),
    path("folders/create/", notes_views.folder_create, name="folder_create"),
    path("folders/<int:pk>/delete/", notes_views.folder_delete, name="folder_delete"),

    # Outline node operations (htmx)
    path("n/<int:pk>/save/", notes_views.node_save, name="node_save"),
    path("n/<int:pk>/create/", notes_views.node_create, name="node_create"),
    path("n/<int:pk>/indent/", notes_views.node_indent, name="node_indent"),
    path("n/<int:pk>/outdent/", notes_views.node_outdent, name="node_outdent"),
    path("n/<int:pk>/delete/", notes_views.node_delete, name="node_delete"),
    path("n/<int:pk>/toggle/", notes_views.node_toggle, name="node_toggle"),

    # Search & tags
    path("search/", notes_views.search, name="search"),
    path("search/results/", notes_views.search_results, name="search_results"),
    path("tags/<str:name>/", notes_views.tag_detail, name="tag_detail"),

    # Flashcards
    path("practice/", flashcards_views.queue, name="queue"),
    path("practice/next/", flashcards_views.queue_next, name="queue_next"),
    path("practice/answer/<int:pk>/", flashcards_views.queue_answer, name="queue_answer"),
    path("cards/", flashcards_views.card_list, name="card_list"),

    # Blog & tutorials
    path("blog/", content_views.blog_index, name="blog_index"),
    path("blog/<slug:slug>/", content_views.blog_post, name="blog_post"),
    path("tutorials/", content_views.tutorials_index, name="tutorials_index"),
    path("tutorials/a/<slug:slug>/", content_views.tutorial_article, name="tutorial_article"),
]
