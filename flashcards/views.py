from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from notes.views import sidebar_context

from .models import Card, ReviewLog


def queue_stats(user):
    now = timezone.now()
    today_start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    due = Card.objects.filter(user=user, due_at__lte=now)
    return {
        "due_count": due.count(),
        "new_count": due.filter(repetitions=0, interval=0).count(),
        "reviewed_today": ReviewLog.objects.filter(card__user=user, reviewed_at__gte=today_start).count(),
        "total_cards": Card.objects.filter(user=user).count(),
    }


def next_due_card(user):
    return Card.objects.filter(user=user, due_at__lte=timezone.now()).order_by("due_at").first()


@login_required
def queue(request):
    return render(
        request,
        "flashcards/queue.html",
        {"stats": queue_stats(request.user), **sidebar_context(request)},
    )


@login_required
def queue_next(request):
    card = next_due_card(request.user)
    return render(
        request,
        "flashcards/_card.html",
        {"card": card, "stats": queue_stats(request.user)},
    )


@login_required
@require_POST
def queue_answer(request, pk):
    card = get_object_or_404(Card, pk=pk, user=request.user)
    try:
        rating = int(request.POST.get("rating", ""))
    except ValueError:
        rating = Card.RATING_GOOD
    if rating not in (Card.RATING_AGAIN, Card.RATING_HARD, Card.RATING_GOOD, Card.RATING_EASY):
        rating = Card.RATING_GOOD
    card.apply_rating(rating)
    next_card = next_due_card(request.user)
    return render(
        request,
        "flashcards/_card.html",
        {"card": next_card, "stats": queue_stats(request.user)},
    )


@login_required
def card_list(request):
    cards = Card.objects.filter(user=request.user).select_related("node", "node__document").order_by("due_at")
    return render(
        request,
        "flashcards/cards.html",
        {"cards": cards, "stats": queue_stats(request.user), "now": timezone.now(), **sidebar_context(request)},
    )
