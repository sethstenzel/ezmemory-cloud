from collections import Counter

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from notes.models import Folder
from notes.views import sidebar_context

from .models import Card, ReviewLog


def descendant_topic_ids(topic):
    """The topic's id plus every descendant subtopic id."""
    children = {}
    for fid, pid in Folder.objects.filter(user=topic.user).values_list("id", "parent_id"):
        children.setdefault(pid, []).append(fid)
    ids, stack = [], [topic.id]
    while stack:
        current = stack.pop()
        ids.append(current)
        stack.extend(children.get(current, []))
    return ids


def scoped_cards(user, topic=None):
    qs = Card.objects.filter(user=user)
    if topic is not None:
        qs = qs.filter(node__document__folder_id__in=descendant_topic_ids(topic))
    return qs


def get_topic(request):
    topic_id = request.GET.get("topic") or None
    if not topic_id:
        return None
    return get_object_or_404(Folder, pk=topic_id, user=request.user)


def queue_stats(user, topic=None):
    now = timezone.now()
    today_start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    cards = scoped_cards(user, topic)
    due = cards.filter(due_at__lte=now)
    return {
        "due_count": due.count(),
        "new_count": due.filter(repetitions=0, interval=0).count(),
        "reviewed_today": ReviewLog.objects.filter(card__user=user, reviewed_at__gte=today_start).count(),
        "total_cards": cards.count(),
    }


def next_due_card(user, topic=None):
    return scoped_cards(user, topic).filter(due_at__lte=timezone.now()).order_by("due_at").first()


def topic_tree_with_due(user):
    """Nested [{topic, due, children}] where due counts include subtopics."""
    now = timezone.now()
    per_topic = Counter(
        Card.objects.filter(user=user, due_at__lte=now)
        .exclude(node__document__folder=None)
        .values_list("node__document__folder_id", flat=True)
    )
    topics = list(Folder.objects.filter(user=user))
    children = {}
    for t in topics:
        children.setdefault(t.parent_id, []).append(t)

    def build(parent_id):
        items = []
        for t in sorted(children.get(parent_id, []), key=lambda f: f.name.lower()):
            kids = build(t.id)
            due = per_topic.get(t.id, 0) + sum(k["due"] for k in kids)
            items.append({"topic": t, "due": due, "children": kids})
        return items

    return build(None)


@login_required
def queue(request):
    return render(
        request,
        "flashcards/queue.html",
        {
            "stats": queue_stats(request.user),
            "topic_tree": topic_tree_with_due(request.user),
            **sidebar_context(request),
        },
    )


@login_required
def queue_next(request):
    topic = get_topic(request)
    return render(
        request,
        "flashcards/_card.html",
        {
            "card": next_due_card(request.user, topic),
            "stats": queue_stats(request.user, topic),
            "topic": topic,
        },
    )


@login_required
@require_POST
def queue_answer(request, pk):
    card = get_object_or_404(Card, pk=pk, user=request.user)
    topic = get_topic(request)
    try:
        rating = int(request.POST.get("rating", ""))
    except ValueError:
        rating = Card.RATING_GOOD
    if rating not in (Card.RATING_AGAIN, Card.RATING_HARD, Card.RATING_GOOD, Card.RATING_EASY):
        rating = Card.RATING_GOOD
    card.apply_rating(rating)
    return render(
        request,
        "flashcards/_card.html",
        {
            "card": next_due_card(request.user, topic),
            "stats": queue_stats(request.user, topic),
            "topic": topic,
        },
    )


@login_required
def card_list(request):
    cards = Card.objects.filter(user=request.user).select_related("node", "node__document").order_by("due_at")
    return render(
        request,
        "flashcards/cards.html",
        {"cards": cards, "stats": queue_stats(request.user), "now": timezone.now(), **sidebar_context(request)},
    )
