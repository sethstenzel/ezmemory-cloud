from django.shortcuts import get_object_or_404, render

from .models import BlogPost, TutorialArticle, TutorialCollection


def blog_index(request):
    posts = list(BlogPost.objects.all())
    featured = next((p for p in posts if p.featured), posts[0] if posts else None)
    latest = [p for p in posts if p != featured]
    return render(request, "content/blog_index.html", {"featured": featured, "posts": latest})


def blog_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    return render(request, "content/blog_post.html", {"post": post})


def tutorials_index(request):
    collections = TutorialCollection.objects.prefetch_related("articles")
    return render(request, "content/tutorials_index.html", {"collections": collections})


def tutorial_article(request, slug):
    article = get_object_or_404(TutorialArticle, slug=slug)
    siblings = list(article.collection.articles.all())
    idx = siblings.index(article)
    prev_article = siblings[idx - 1] if idx > 0 else None
    next_article = siblings[idx + 1] if idx < len(siblings) - 1 else None
    return render(
        request,
        "content/tutorial_article.html",
        {"article": article, "prev_article": prev_article, "next_article": next_article},
    )
